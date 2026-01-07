"use client";

import React from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  StochasticParameters,
  KeltnerChannelParameters,
  ATRTrailingStopParameters,
  DonchianChannelParameters,
  IchimokuCloudParameters,
} from "@/types";

interface StrategyParametersProps {
  strategyType: string;
  parameters: Record<string, any>;
  onChange: (parameters: Record<string, any>) => void;
}

export function StrategyParameters({
  strategyType,
  parameters,
  onChange,
}: StrategyParametersProps) {
  const updateParameter = (key: string, value: any) => {
    onChange({ ...parameters, [key]: value });
  };

  const renderStochasticParameters = () => {
    const params = parameters as StochasticParameters;
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="k_period">
              %K Period
              <span className="text-xs text-muted-foreground ml-2">(default: 14)</span>
            </Label>
            <Input
              id="k_period"
              type="number"
              min="1"
              max="100"
              value={params.k_period ?? 14}
              onChange={(e) => updateParameter("k_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Lookback period for %K calculation
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="d_period">
              %D Period
              <span className="text-xs text-muted-foreground ml-2">(default: 3)</span>
            </Label>
            <Input
              id="d_period"
              type="number"
              min="1"
              max="20"
              value={params.d_period ?? 3}
              onChange={(e) => updateParameter("d_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              %D smoothing period (moving average of %K)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="smooth_k">
              Smooth %K
              <span className="text-xs text-muted-foreground ml-2">(default: 3)</span>
            </Label>
            <Input
              id="smooth_k"
              type="number"
              min="1"
              max="10"
              value={params.smooth_k ?? 3}
              onChange={(e) => updateParameter("smooth_k", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Slow %K smoothing period
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="oversold">
              Oversold Level
              <span className="text-xs text-muted-foreground ml-2">(default: 20)</span>
            </Label>
            <Input
              id="oversold"
              type="number"
              min="0"
              max="100"
              value={params.oversold ?? 20}
              onChange={(e) => updateParameter("oversold", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Buy signals generated below this level
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="overbought">
              Overbought Level
              <span className="text-xs text-muted-foreground ml-2">(default: 80)</span>
            </Label>
            <Input
              id="overbought"
              type="number"
              min="0"
              max="100"
              value={params.overbought ?? 80}
              onChange={(e) => updateParameter("overbought", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Sell signals generated above this level
            </p>
          </div>
        </div>
      </div>
    );
  };

  const renderKeltnerChannelParameters = () => {
    const params = parameters as KeltnerChannelParameters;
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="ema_period">
              EMA Period
              <span className="text-xs text-muted-foreground ml-2">(default: 20)</span>
            </Label>
            <Input
              id="ema_period"
              type="number"
              min="1"
              max="200"
              value={params.ema_period ?? 20}
              onChange={(e) => updateParameter("ema_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Period for middle line EMA
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="atr_period">
              ATR Period
              <span className="text-xs text-muted-foreground ml-2">(default: 10)</span>
            </Label>
            <Input
              id="atr_period"
              type="number"
              min="1"
              max="100"
              value={params.atr_period ?? 10}
              onChange={(e) => updateParameter("atr_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              ATR period for calculating band width
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="multiplier">
              Multiplier
              <span className="text-xs text-muted-foreground ml-2">(default: 2.0)</span>
            </Label>
            <Input
              id="multiplier"
              type="number"
              min="0.1"
              max="10"
              step="0.1"
              value={params.multiplier ?? 2.0}
              onChange={(e) => updateParameter("multiplier", parseFloat(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Band width multiplier (higher = wider bands)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="use_breakout" className="flex items-center gap-2">
              <input
                id="use_breakout"
                type="checkbox"
                checked={params.use_breakout ?? true}
                onChange={(e) => updateParameter("use_breakout", e.target.checked)}
                className="w-4 h-4 rounded border-gray-300"
              />
              Breakout Mode
            </Label>
            <p className="text-xs text-muted-foreground">
              {params.use_breakout ?? true
                ? "Breakout: Buy above upper band, sell below lower band"
                : "Mean Reversion: Buy at lower band, sell at upper band"}
            </p>
          </div>
        </div>
      </div>
    );
  };

  const renderATRTrailingStopParameters = () => {
    const params = parameters as ATRTrailingStopParameters;
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="atr_period">
              ATR Period
              <span className="text-xs text-muted-foreground ml-2">(default: 14)</span>
            </Label>
            <Input
              id="atr_period"
              type="number"
              min="1"
              max="100"
              value={params.atr_period ?? 14}
              onChange={(e) => updateParameter("atr_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              ATR calculation period
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="atr_multiplier">
              ATR Multiplier
              <span className="text-xs text-muted-foreground ml-2">(default: 3.0)</span>
            </Label>
            <Input
              id="atr_multiplier"
              type="number"
              min="0.1"
              max="10"
              step="0.1"
              value={params.atr_multiplier ?? 3.0}
              onChange={(e) => updateParameter("atr_multiplier", parseFloat(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Stop distance multiplier (higher = wider stops)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="trend_period">
              Trend Period
              <span className="text-xs text-muted-foreground ml-2">(default: 50)</span>
            </Label>
            <Input
              id="trend_period"
              type="number"
              min="1"
              max="200"
              value={params.trend_period ?? 50}
              onChange={(e) => updateParameter("trend_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Trend filter EMA period
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="use_chandelier" className="flex items-center gap-2">
              <input
                id="use_chandelier"
                type="checkbox"
                checked={params.use_chandelier ?? true}
                onChange={(e) => updateParameter("use_chandelier", e.target.checked)}
                className="w-4 h-4 rounded border-gray-300"
              />
              Use Chandelier Exit
            </Label>
            <p className="text-xs text-muted-foreground">
              {params.use_chandelier ?? true
                ? "Chandelier: Stop from highest high"
                : "Simple: Stop from close price"}
            </p>
          </div>
        </div>
      </div>
    );
  };

  const renderDonchianChannelParameters = () => {
    const params = parameters as DonchianChannelParameters;
    const isSystem2 = params.use_system_2 ?? false;

    return (
      <div className="space-y-4">
        <div className="space-y-2 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <Label htmlFor="use_system_2" className="flex items-center gap-2">
            <input
              id="use_system_2"
              type="checkbox"
              checked={isSystem2}
              onChange={(e) => {
                const useSystem2 = e.target.checked;
                updateParameter("use_system_2", useSystem2);
                // Auto-update periods when switching systems
                if (useSystem2) {
                  updateParameter("entry_period", 55);
                  updateParameter("exit_period", 20);
                } else {
                  updateParameter("entry_period", 20);
                  updateParameter("exit_period", 10);
                }
              }}
              className="w-4 h-4 rounded border-gray-300"
            />
            <span className="font-semibold">
              {isSystem2 ? "System 2 (Slow)" : "System 1 (Fast)"}
            </span>
          </Label>
          <p className="text-xs text-muted-foreground">
            {isSystem2
              ? "System 2: 55-day entry, 20-day exit - Slower, fewer trades"
              : "System 1: 20-day entry, 10-day exit - Faster, more trades"}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="entry_period">
              Entry Period
              <span className="text-xs text-muted-foreground ml-2">
                (System 1: 20, System 2: 55)
              </span>
            </Label>
            <Input
              id="entry_period"
              type="number"
              min="1"
              max="200"
              value={params.entry_period ?? (isSystem2 ? 55 : 20)}
              onChange={(e) => updateParameter("entry_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Breakout entry period (highest high)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="exit_period">
              Exit Period
              <span className="text-xs text-muted-foreground ml-2">
                (System 1: 10, System 2: 20)
              </span>
            </Label>
            <Input
              id="exit_period"
              type="number"
              min="1"
              max="100"
              value={params.exit_period ?? (isSystem2 ? 20 : 10)}
              onChange={(e) => updateParameter("exit_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Exit period (lowest low)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="atr_period">
              ATR Period
              <span className="text-xs text-muted-foreground ml-2">(default: 20)</span>
            </Label>
            <Input
              id="atr_period"
              type="number"
              min="1"
              max="100"
              value={params.atr_period ?? 20}
              onChange={(e) => updateParameter("atr_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              ATR period for stop-loss calculation
            </p>
          </div>
        </div>

        <div className="p-3 bg-amber-50 border border-amber-200 rounded text-sm text-amber-900">
          <strong>Turtle Trading System:</strong> The famous Richard Dennis experiment.
          System 1 is faster with more signals, System 2 is slower and more selective.
        </div>
      </div>
    );
  };

  const renderIchimokuCloudParameters = () => {
    const params = parameters as IchimokuCloudParameters;
    return (
      <div className="space-y-4">
        <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-900">
          <strong>Ichimoku Cloud:</strong> A comprehensive Japanese charting system.
          The standard settings (9, 26, 52) are based on Japanese market trading days.
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="tenkan_period">
              Tenkan-sen (Conversion Line)
              <span className="text-xs text-muted-foreground ml-2">(default: 9)</span>
            </Label>
            <Input
              id="tenkan_period"
              type="number"
              min="1"
              max="100"
              value={params.tenkan_period ?? 9}
              onChange={(e) => updateParameter("tenkan_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              9-period midpoint (fast line)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="kijun_period">
              Kijun-sen (Base Line)
              <span className="text-xs text-muted-foreground ml-2">(default: 26)</span>
            </Label>
            <Input
              id="kijun_period"
              type="number"
              min="1"
              max="200"
              value={params.kijun_period ?? 26}
              onChange={(e) => updateParameter("kijun_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              26-period midpoint (slow line)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="senkou_b_period">
              Senkou Span B Period
              <span className="text-xs text-muted-foreground ml-2">(default: 52)</span>
            </Label>
            <Input
              id="senkou_b_period"
              type="number"
              min="1"
              max="200"
              value={params.senkou_b_period ?? 52}
              onChange={(e) => updateParameter("senkou_b_period", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Leading Span B period (cloud boundary)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="displacement">
              Displacement
              <span className="text-xs text-muted-foreground ml-2">(default: 26)</span>
            </Label>
            <Input
              id="displacement"
              type="number"
              min="1"
              max="100"
              value={params.displacement ?? 26}
              onChange={(e) => updateParameter("displacement", parseInt(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Cloud displacement (forward shift)
            </p>
          </div>
        </div>

        <div className="p-3 bg-green-50 border border-green-200 rounded text-sm">
          <p className="font-semibold text-green-900 mb-1">Signal Types:</p>
          <ul className="text-green-800 space-y-1 text-xs">
            <li>• <strong>Strong Buy:</strong> TK cross up + price above cloud + bullish cloud</li>
            <li>• <strong>Weak Buy:</strong> TK cross up only</li>
            <li>• <strong>Strong Sell:</strong> TK cross down + price below cloud + bearish cloud</li>
            <li>• <strong>Weak Sell:</strong> TK cross down only</li>
          </ul>
        </div>
      </div>
    );
  };

  // Render appropriate parameter form based on strategy type
  const renderParameters = () => {
    switch (strategyType) {
      case "stochastic":
        return renderStochasticParameters();
      case "keltner_channel":
        return renderKeltnerChannelParameters();
      case "atr_trailing_stop":
        return renderATRTrailingStopParameters();
      case "donchian_channel":
        return renderDonchianChannelParameters();
      case "ichimoku_cloud":
        return renderIchimokuCloudParameters();
      default:
        return (
          <div className="p-4 bg-gray-50 border border-gray-200 rounded text-sm text-gray-600">
            No additional parameters required for this strategy type.
            Default parameters will be used.
          </div>
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="border-b pb-2">
        <h3 className="text-lg font-semibold">Strategy Parameters</h3>
        <p className="text-sm text-muted-foreground">
          Configure the parameters for your selected strategy
        </p>
      </div>
      {renderParameters()}
    </div>
  );
}
