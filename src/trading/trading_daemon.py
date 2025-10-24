"""
Trading Daemon - Background Process

Runs continuously to:
1. Monitor trading state
2. Execute strategies automatically
3. Persist state across restarts
4. Independent of UI
"""

import logging
import time
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict
import traceback

from src.trading.state_manager import StateManager
from src.trading.live_trader import LiveTrader
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.bollinger_bands import BollingerBandsStrategy
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.breakout_strategy import BreakoutStrategy
from src.strategies.vwap_strategy import VWAPStrategy
from src.strategies.pairs_trading import PairsTradingStrategy
from src.strategies.ml_strategy import MLStrategy
from src.strategies.adaptive_ml_strategy import AdaptiveMLStrategy


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/trading_daemon.log'),
        logging.StreamHandler()
    ]
)


class TradingDaemon:
    """Background trading daemon that runs independently."""
    
    def __init__(self):
        """Initialize trading daemon."""
        self.logger = logging.getLogger(__name__)
        self.state_manager = StateManager()
        self.trader = None
        self.running = False
        
        # All available strategies
        self.all_strategies = {
            'SMA Crossover': SMACrossoverStrategy,
            'RSI': RSIStrategy,
            'MACD': MACDStrategy,
            'Bollinger Bands': BollingerBandsStrategy,
            'Momentum': MomentumStrategy,
            'Mean Reversion': MeanReversionStrategy,
            'Breakout': BreakoutStrategy,
            'VWAP': VWAPStrategy,
            'Pairs Trading': PairsTradingStrategy,
            'ML Strategy': MLStrategy,
            'Adaptive ML': AdaptiveMLStrategy
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Trading Daemon initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _get_strategy_instances(self) -> Dict:
        """Get instances of all strategies."""
        return {name: cls() for name, cls in self.all_strategies.items()}
    
    def _load_or_create_trader(self, config: Dict):
        """Load or create trader with current configuration."""
        # Get all strategy instances
        strategies = self._get_strategy_instances()
        
        # Create trader
        self.trader = LiveTrader(
            strategies=strategies,
            symbols=config['tickers'],
            initial_capital=config['initial_capital'],
            paper_trading=config['paper_trading'],
            risk_per_trade=config['risk_per_trade'],
            max_positions=config['max_positions']
        )
        
        self.logger.info(f"Trader created with {len(config['tickers'])} tickers")
    
    def _ensure_strategies_evaluated(self, config: Dict, metric: str = 'sharpe_ratio'):
        """Ensure all strategies have been evaluated for all tickers."""
        need_evaluation = []
        
        for ticker in config['tickers']:
            best_strategy = self.state_manager.get_best_strategy(ticker)
            if not best_strategy:
                need_evaluation.append(ticker)
        
        if need_evaluation:
            self.logger.info(f"Need to evaluate strategies for: {', '.join(need_evaluation)}")
            self._evaluate_strategies(need_evaluation, config, metric)
        else:
            self.logger.info("All tickers have strategy evaluations")
            # Load best strategies into trader
            self._load_best_strategies(config['tickers'])
    
    def _evaluate_strategies(self, tickers: list, config: Dict, metric: str):
        """Evaluate all strategies for given tickers using ALL available historical data."""
        self.logger.info(f"Evaluating {len(self.all_strategies)} strategies on {len(tickers)} tickers...")
        self.logger.info("Using ALL available historical data (up to 20 years)")
        
        # Pass None to use all available data
        results = self.trader.evaluate_strategies(
            lookback_days=None,
            metric=metric
        )
        
        # Save results to state manager
        for ticker, data in results.items():
            # Save all strategy results
            for strategy_name, strategy_result in data['all_results'].items():
                self.state_manager.save_strategy_evaluation(
                    ticker=ticker,
                    strategy_name=strategy_name,
                    metrics=strategy_result['metrics'],
                    score=strategy_result['score'],
                    metric_name=metric
                )
            
            # Save best strategy
            self.state_manager.save_best_strategy(
                ticker=ticker,
                strategy_name=data['best_strategy'],
                score=data['best_score'],
                metric_name=metric
            )
            
            self.logger.info(f"✓ Best for {ticker}: {data['best_strategy']} ({metric}={data['best_score']:.3f})")
    
    def _load_best_strategies(self, tickers: list):
        """Load best strategies from state manager into trader."""
        for ticker in tickers:
            best_strategy_info = self.state_manager.get_best_strategy(ticker)
            if best_strategy_info:
                strategy_name = best_strategy_info['strategy_name']
                strategy_class = self.all_strategies.get(strategy_name)
                if strategy_class:
                    self.trader.best_strategies[ticker] = strategy_class()
                    self.logger.info(f"Loaded {strategy_name} for {ticker}")
    
    def _execute_trading_cycle(self, config: Dict):
        """Execute one trading cycle."""
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting trading cycle...")
            
            # Get current signals
            signals = self.trader.get_current_signals()
            
            # Log signals
            for ticker, signal in signals.items():
                signal_str = "BUY" if signal == 1 else "SELL" if signal == -1 else "HOLD"
                best_strat_info = self.state_manager.get_best_strategy(ticker)
                strategy_name = best_strat_info['strategy_name'] if best_strat_info else "Unknown"
                self.logger.info(f"  {ticker} ({strategy_name}): {signal_str}")
            
            # Execute trades
            trades = self.trader.execute_trades(signals)
            
            # Record trades in state manager
            for trade in trades:
                strategy_info = self.state_manager.get_best_strategy(trade['symbol'])
                strategy_name = strategy_info['strategy_name'] if strategy_info else "Unknown"
                
                self.state_manager.record_trade(
                    ticker=trade['symbol'],
                    strategy_name=strategy_name,
                    action=trade['action'],
                    quantity=trade['qty'],
                    price=trade['price'],
                    signal=signals.get(trade['symbol'], 0),
                    order_id=trade.get('order_id')
                )
                
                self.logger.info(f"✓ Executed: {trade['action']} {trade['qty']} {trade['symbol']} @ ${trade['price']:.2f}")
            
            if not trades:
                self.logger.info("No trades executed (all HOLD or positions full)")
            
            # Update last check time
            self.state_manager.update_last_check()
            
            self.logger.info("Trading cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")
            self.logger.error(traceback.format_exc())
    
    def run(self):
        """Main daemon loop."""
        self.running = True
        self.logger.info("Trading Daemon starting...")
        
        while self.running:
            try:
                # Check if trading is active
                if not self.state_manager.is_trading_active():
                    self.logger.info("Trading is not active, waiting...")
                    time.sleep(30)  # Check every 30 seconds
                    continue
                
                # Get trading configuration
                config = self.state_manager.get_trading_config()
                if not config:
                    self.logger.warning("No trading configuration found, waiting...")
                    time.sleep(30)
                    continue
                
                # Create/update trader if needed
                if not self.trader:
                    self._load_or_create_trader(config)
                
                # Ensure strategies are evaluated
                self._ensure_strategies_evaluated(config)
                
                # Execute trading cycle
                self._execute_trading_cycle(config)
                
                # Sleep until next check
                check_interval = config.get('check_interval', 300)
                self.logger.info(f"Next check in {check_interval} seconds...")
                
                # Sleep in small intervals to allow for responsive shutdown
                for _ in range(check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                self.logger.error(traceback.format_exc())
                time.sleep(60)  # Wait a bit before retrying
        
        self.logger.info("Trading Daemon stopped")


def main():
    """Main entry point for daemon."""
    daemon = TradingDaemon()
    try:
        daemon.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
