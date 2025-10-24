'use client';

import { useParams } from 'next/navigation';
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  useExecutionStatus,
  useSignals,
  usePerformance,
  useStartExecution,
  useStopExecution,
  useResetExecution,
} from '@/lib/hooks/use-execution';
import { Play, Square, RotateCcw, TrendingUp, TrendingDown, Activity } from 'lucide-react';

export default function StrategyExecutionPage() {
  const params = useParams();
  const strategyId = params.id as string;

  const { data: status, isLoading: statusLoading } = useExecutionStatus(strategyId);
  const { data: signals, isLoading: signalsLoading } = useSignals(strategyId, 50);
  const { data: performance, isLoading: perfLoading } = usePerformance(strategyId, 30);

  const startMutation = useStartExecution();
  const stopMutation = useStopExecution();
  const resetMutation = useResetExecution();

  const handleStart = () => startMutation.mutate(strategyId);
  const handleStop = () => stopMutation.mutate(strategyId);
  const handleReset = () => {
    if (confirm('Are you sure you want to reset? This will clear all execution data.')) {
      resetMutation.mutate(strategyId);
    }
  };

  if (statusLoading) {
    return <div className="flex items-center justify-center h-96">Loading...</div>;
  }

  const isActive = status?.is_active || false;
  const statusColor = isActive ? 'bg-green-500' : 'bg-gray-500';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Strategy Execution</h1>
          <p className="text-muted-foreground">Monitor and control live strategy execution</p>
        </div>
        <div className="flex gap-2">
          {!isActive ? (
            <Button onClick={handleStart} disabled={startMutation.isPending}>
              <Play className="mr-2 h-4 w-4" />
              Start Execution
            </Button>
          ) : (
            <Button variant="destructive" onClick={handleStop} disabled={stopMutation.isPending}>
              <Square className="mr-2 h-4 w-4" />
              Stop Execution
            </Button>
          )}
          <Button variant="outline" onClick={handleReset} disabled={resetMutation.isPending}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset
          </Button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${statusColor}`} />
              <span className="text-2xl font-bold">{isActive ? 'Running' : 'Stopped'}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {status?.state || 'Idle'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            {status && status.total_pnl >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-500" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${status?.total_pnl?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Current: ${status?.current_pnl?.toFixed(2) || '0.00'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status?.total_trades || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Today: {status?.trades_today || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status?.win_rate?.toFixed(1) || '0'}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {status?.total_trades || 0} total trades
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Signals Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Signals</CardTitle>
          <CardDescription>Latest trading signals generated by the strategy</CardDescription>
        </CardHeader>
        <CardContent>
          {signalsLoading ? (
            <div>Loading signals...</div>
          ) : !signals || signals.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No signals generated yet
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Time</th>
                    <th className="text-left p-2">Type</th>
                    <th className="text-left p-2">Symbol</th>
                    <th className="text-right p-2">Price</th>
                    <th className="text-left p-2">Reasoning</th>
                    <th className="text-center p-2">Executed</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map((signal: any) => (
                    <tr key={signal.id} className="border-b hover:bg-muted/50">
                      <td className="p-2 text-sm">
                        {new Date(signal.timestamp).toLocaleString()}
                      </td>
                      <td className="p-2">
                        <Badge variant={signal.signal_type === 'BUY' ? 'default' : 'destructive'}>
                          {signal.signal_type}
                        </Badge>
                      </td>
                      <td className="p-2 font-medium">{signal.symbol}</td>
                      <td className="p-2 text-right">${signal.price.toFixed(2)}</td>
                      <td className="p-2 text-sm text-muted-foreground">
                        {signal.reasoning}
                      </td>
                      <td className="p-2 text-center">
                        {signal.executed ? '✓' : '○'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      {performance && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Summary</CardTitle>
            <CardDescription>Last 30 days performance metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <div className="text-sm font-medium text-muted-foreground">Win Rate</div>
                <div className="text-2xl font-bold">
                  {performance.performance.win_rate.toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground">Total Trades</div>
                <div className="text-2xl font-bold">
                  {performance.performance.total_trades}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground">Net P&L</div>
                <div className={`text-2xl font-bold ${performance.performance.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  ${performance.performance.total_pnl.toFixed(2)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
