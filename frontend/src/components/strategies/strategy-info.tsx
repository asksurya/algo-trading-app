"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Info, TrendingUp, TrendingDown, Activity, BarChart3, Cloud } from "lucide-react";

interface StrategyInfoProps {
  strategyType: string;
}

export function StrategyInfo({ strategyType }: StrategyInfoProps) {
  const getStrategyInfo = () => {
    switch (strategyType) {
      case "stochastic":
        return {
          icon: <Activity className="h-5 w-5" />,
          name: "Stochastic Oscillator",
          description:
            "A momentum oscillator that compares a closing price to its price range over a given period. Useful for identifying overbought and oversold conditions.",
          signals: [
            "BUY: %K crosses above %D in oversold zone (<20)",
            "SELL: %K crosses below %D in overbought zone (>80)",
          ],
          bestFor: "Range-bound markets, mean reversion",
          category: "Oscillator",
          color: "blue",
        };

      case "keltner_channel":
        return {
          icon: <BarChart3 className="h-5 w-5" />,
          name: "Keltner Channel",
          description:
            "A volatility-based indicator using EMA and ATR to create dynamic price channels. Can be used for both breakout and mean reversion strategies.",
          signals: [
            "Breakout Mode: BUY above upper band, SELL below lower band",
            "Mean Reversion Mode: BUY at lower band, SELL at upper band",
          ],
          bestFor: "Trending markets (breakout) or ranging markets (mean reversion)",
          category: "Volatility Channel",
          color: "purple",
        };

      case "atr_trailing_stop":
        return {
          icon: <TrendingUp className="h-5 w-5" />,
          name: "ATR Trailing Stop",
          description:
            "A trend-following system that uses ATR (Average True Range) to dynamically adjust stop-loss levels. Excellent for protecting profits in trending markets.",
          signals: [
            "BUY: Price crosses above trend EMA",
            "SELL: Price crosses below trailing stop",
          ],
          bestFor: "Strong trending markets, risk management",
          category: "Trend Following",
          color: "green",
        };

      case "donchian_channel":
        return {
          icon: <TrendingUp className="h-5 w-5" />,
          name: "Donchian Channel (Turtle Trading)",
          description:
            "The famous Turtle Trading system by Richard Dennis. Trades breakouts of the highest high or lowest low over a specified period. Two variants: System 1 (fast) and System 2 (slow).",
          signals: [
            "BUY: Price breaks above N-day high",
            "SELL: Price breaks below exit period low",
          ],
          bestFor: "Trending markets, breakout trading",
          category: "Breakout System",
          color: "amber",
          note: "Made $175 million in 5 years for the original Turtles!",
        };

      case "ichimoku_cloud":
        return {
          icon: <Cloud className="h-5 w-5" />,
          name: "Ichimoku Cloud",
          description:
            "A comprehensive Japanese charting system with 5 components that provides a complete view of support, resistance, momentum, and trend direction at a glance.",
          signals: [
            "Strong BUY: TK cross up + price above cloud + bullish cloud",
            "Weak BUY: TK cross up only",
            "Strong SELL: TK cross down + price below cloud + bearish cloud",
            "Weak SELL: TK cross down only",
          ],
          bestFor: "All market conditions, comprehensive analysis",
          category: "Multi-Indicator System",
          color: "indigo",
          note: "Developed in 1940s Japan, very popular globally",
        };

      // Original strategies
      case "momentum":
        return {
          icon: <TrendingUp className="h-5 w-5" />,
          name: "Momentum",
          description: "Follows the direction and strength of price movement",
          category: "Trend Following",
          color: "green",
        };

      case "mean_reversion":
        return {
          icon: <TrendingDown className="h-5 w-5" />,
          name: "Mean Reversion",
          description: "Trades when prices deviate from their average",
          category: "Mean Reversion",
          color: "blue",
        };

      case "rsi":
        return {
          icon: <Activity className="h-5 w-5" />,
          name: "RSI (Relative Strength Index)",
          description: "Momentum oscillator measuring overbought/oversold conditions",
          category: "Oscillator",
          color: "purple",
        };

      default:
        return null;
    }
  };

  const info = getStrategyInfo();

  if (!info) return null;

  const colorClasses = {
    blue: "bg-blue-50 border-blue-200 text-blue-900",
    purple: "bg-purple-50 border-purple-200 text-purple-900",
    green: "bg-green-50 border-green-200 text-green-900",
    amber: "bg-amber-50 border-amber-200 text-amber-900",
    indigo: "bg-indigo-50 border-indigo-200 text-indigo-900",
  };

  const categoryBadgeColors = {
    blue: "bg-blue-100 text-blue-800",
    purple: "bg-purple-100 text-purple-800",
    green: "bg-green-100 text-green-800",
    amber: "bg-amber-100 text-amber-800",
    indigo: "bg-indigo-100 text-indigo-800",
  };

  return (
    <Card className={`p-4 border ${colorClasses[info.color as keyof typeof colorClasses]}`}>
      <div className="flex items-start gap-3">
        <div className="mt-1">{info.icon}</div>
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <h4 className="font-bold text-base">{info.name}</h4>
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                categoryBadgeColors[info.color as keyof typeof categoryBadgeColors]
              }`}
            >
              {info.category}
            </span>
          </div>

          <p className="text-sm">{info.description}</p>

          {info.signals && (
            <div className="space-y-1">
              <p className="text-xs font-semibold">Signals:</p>
              <ul className="text-xs space-y-0.5">
                {info.signals.map((signal, idx) => (
                  <li key={idx}>• {signal}</li>
                ))}
              </ul>
            </div>
          )}

          {info.bestFor && (
            <p className="text-xs">
              <strong>Best for:</strong> {info.bestFor}
            </p>
          )}

          {info.note && (
            <div className="flex items-start gap-2 mt-2 p-2 bg-white/50 rounded">
              <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <p className="text-xs font-medium">{info.note}</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
