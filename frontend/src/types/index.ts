/**
 * TypeScript type definitions for the application.
 * These match the backend API schemas.
 */

// User types
export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: 'admin' | 'user' | 'viewer';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Strategy types
export interface Strategy {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  strategy_type: string;
  parameters: Record<string, any>;
  is_active: boolean;
  is_backtested: boolean;
  backtest_results?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface StrategyCreate {
  name: string;
  description?: string;
  strategy_type: string;
  parameters: Record<string, any>;
  tickers?: string[];
}

export interface StrategyTicker {
  id: string;
  strategy_id: string;
  ticker: string;
  allocation_percent?: number;
  is_active: boolean;
  created_at: string;
}

// Trade types
export type TradeType = 'buy' | 'sell';
export type TradeStatus = 'pending' | 'filled' | 'partially_filled' | 'cancelled' | 'rejected';

export interface Trade {
  id: string;
  user_id: string;
  strategy_id?: string;
  ticker: string;
  trade_type: TradeType;
  status: TradeStatus;
  quantity: string;
  filled_quantity: string;
  price?: string;
  filled_avg_price?: string;
  order_id?: string;
  realized_pnl?: string;
  created_at: string;
  executed_at?: string;
}

export interface TradeCreate {
  ticker: string;
  trade_type: TradeType;
  quantity: string;
  price?: string;
  strategy_id?: string;
}

export interface Position {
  id: string;
  user_id: string;
  strategy_id?: string;
  ticker: string;
  quantity: string;
  avg_entry_price: string;
  current_price?: string;
  unrealized_pnl?: string;
  realized_pnl: string;
  opened_at: string;
  updated_at: string;
  closed_at?: string;
}

export interface TradingStatistics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: string;
  avg_win?: string;
  avg_loss?: string;
  largest_win?: string;
  largest_loss?: string;
  sharpe_ratio?: number;
}

export interface PortfolioSummary {
  total_value: string;
  cash_balance: string;
  positions_value: string;
  total_pnl: string;
  day_pnl: string;
  positions_count: number;
  active_strategies: number;
}

// API Error types
export interface APIError {
  detail: string;
  status?: number;
}

// Backtest types
export interface Backtest {
  id: string;
  user_id: string;
  strategy_id: string;
  name: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  status: 'running' | 'completed' | 'failed';
  total_return?: number;
  total_trades?: number;
  win_rate?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  created_at: string;
  results?: BacktestResults;
  trades?: BacktestTrade[];
}

export interface BacktestResults {
  total_return_pct: number;
  net_profit: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  sharpe_ratio?: number;
  final_capital: number;
  gross_profit: number;
  gross_loss: number;
  max_drawdown_pct: number;
  avg_trade_pnl: number;
}

export interface BacktestTrade {
    id: string;
    symbol: string;
    side: 'buy' | 'sell';
    quantity: number;
    entry_price: number;
    exit_price?: number;
    pnl?: number;
    pnl_pct?: number;
    entry_date: string;
}

export interface BacktestCreate {
  strategy_id: string;
  name: string;
  description?: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission: number;
  slippage: number;
}

export type LiveStrategyStatus = 'ACTIVE' | 'STOPPED' | 'PAUSED' | 'ERROR' | 'inactive' | 'running' | 'paused' | 'error';

export interface LiveStrategy {
    id: string;
    name: string;
    strategy_id: number;
    user_id: string;
    symbols: string[];
    check_interval: number;
    auto_execute: boolean;
    max_positions: number;
    daily_loss_limit?: number;
    position_size_pct: number;
    max_position_size?: number;
    is_active: boolean;
    status: LiveStrategyStatus;
    total_signals: number;
    executed_trades: number;
    current_positions: number;
    daily_pnl: number;
    error_message?: string;
    created_at: string;
    updated_at: string;
}

export interface LivePosition {
    id: string;
    live_strategy_id: string;
    symbol: string;
    quantity: number;
    avg_entry_price: number;
    current_price: number;
    unrealized_pnl: number;
    status: 'open' | 'closed';
    created_at: string;
    updated_at: string;
}

export interface PaginatedBacktests {
  data: Backtest[];
  page: number;
  limit: number;
  total: number;
}

// Strategy type constants
export const STRATEGY_TYPES = {
  // Original strategies
  MOMENTUM: 'momentum',
  MEAN_REVERSION: 'mean_reversion',
  MACD: 'macd',
  RSI: 'rsi',
  BOLLINGER_BANDS: 'bollinger_bands',
  SMA_CROSSOVER: 'sma_crossover',
  BREAKOUT: 'breakout',
  VWAP: 'vwap',
  PAIRS_TRADING: 'pairs_trading',
  ML_STRATEGY: 'ml_strategy',
  ADAPTIVE_ML: 'adaptive_ml',
  // New strategies (5)
  STOCHASTIC: 'stochastic',
  KELTNER_CHANNEL: 'keltner_channel',
  ATR_TRAILING_STOP: 'atr_trailing_stop',
  DONCHIAN_CHANNEL: 'donchian_channel',
  ICHIMOKU_CLOUD: 'ichimoku_cloud',
} as const;

export type StrategyType = typeof STRATEGY_TYPES[keyof typeof STRATEGY_TYPES];

// Strategy parameter type definitions
export interface StochasticParameters {
  k_period?: number;       // %K lookback period (default: 14)
  d_period?: number;       // %D smoothing period (default: 3)
  smooth_k?: number;       // Slow %K smoothing (default: 3)
  oversold?: number;       // Oversold threshold (default: 20)
  overbought?: number;     // Overbought threshold (default: 80)
}

export interface KeltnerChannelParameters {
  ema_period?: number;     // Middle line EMA period (default: 20)
  atr_period?: number;     // ATR for band width (default: 10)
  multiplier?: number;     // Band width multiplier (default: 2.0)
  use_breakout?: boolean;  // Breakout vs mean reversion mode (default: true)
}

export interface ATRTrailingStopParameters {
  atr_period?: number;         // ATR calculation period (default: 14)
  atr_multiplier?: number;     // Stop distance multiplier (default: 3.0)
  trend_period?: number;       // Trend filter EMA period (default: 50)
  use_chandelier?: boolean;    // Chandelier Exit method (default: true)
}

export interface DonchianChannelParameters {
  entry_period?: number;   // Breakout entry period (default: 20, System 2: 55)
  exit_period?: number;    // Exit period (default: 10, System 2: 20)
  atr_period?: number;     // ATR for stop-loss (default: 20)
  use_system_2?: boolean;  // Toggle between System 1 (fast) and System 2 (slow) (default: false)
}

export interface IchimokuCloudParameters {
  tenkan_period?: number;    // Conversion Line period (default: 9)
  kijun_period?: number;     // Base Line period (default: 26)
  senkou_b_period?: number;  // Leading Span B period (default: 52)
  displacement?: number;     // Cloud displacement (default: 26)
}

// Union type for all strategy parameters
export type StrategyParameters =
  | StochasticParameters
  | KeltnerChannelParameters
  | ATRTrailingStopParameters
  | DonchianChannelParameters
  | IchimokuCloudParameters
  | Record<string, any>;
