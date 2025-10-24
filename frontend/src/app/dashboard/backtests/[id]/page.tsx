'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useBacktest } from '@/lib/hooks/use-backtests';
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';

export default function BacktestResultsPage() {
  const params = useParams();
  const backtestId = params.id as string;
  const { data, isLoading } = useBacktest(backtestId, true);

  if (isLoading) {
    return <div className="flex items-center justify-center h-96">Loading...</div>;
  }

  const backtest = data?.data;
  
  if (!backtest) {
    return <div className="text-center py-12">Backtest not found</div>;
  }

  const results = backtest.results;
  const trades = backtest.trades || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/backtests">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{backtest.name}</h1>
          <p className="text-muted-foreground">
            {new Date(backtest.start_date).toLocaleDateString()} -{' '}
            {new Date(backtest.end_date).toLocaleDateString()}
          </p>
        </div>
        <Badge
          variant={
            backtest.status === 'completed'
              ? 'default'
              : backtest.status === 'running'
              ? 'secondary'
              : 'destructive'
          }
        >
          {backtest.status}
        </Badge>
      </div>

      {/* Performance Summary */}
      {results && (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Return</CardTitle>
                {results.total_return_pct >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500" />
                )}
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${results.total_return_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {results.total_return_pct.toFixed(2)}%
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  ${results.net_profit.toFixed(2)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{results.total_trades}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {results.winning_trades}W / {results.losing_trades}L
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{results.win_rate.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {results.winning_trades} winning trades
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {results.sharpe_ratio ? results.sharpe_ratio.toFixed(2) : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Risk-adjusted return
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Metrics</CardTitle>
              <CardDescription>Comprehensive performance analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-3">
                <div>
                  <h4 className="font-semibold mb-3">Capital</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Initial:</span>
                      <span className="font-medium">${backtest.initial_capital.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Final:</span>
                      <span className="font-medium">${results.final_capital.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">P&L</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gross Profit:</span>
                      <span className="font-medium text-green-500">${results.gross_profit.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gross Loss:</span>
                      <span className="font-medium text-red-500">${results.gross_loss.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span className="text-muted-foreground">Net P&L:</span>
                      <span className={`font-bold ${results.net_profit >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        ${results.net_profit.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">Risk Metrics</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Max Drawdown:</span>
                      <span className="font-medium text-red-500">{results.max_drawdown_pct.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Avg Trade:</span>
                      <span className="font-medium">${results.avg_trade_pnl.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Trade History */}
      <Card>
        <CardHeader>
          <CardTitle>Trade History</CardTitle>
          <CardDescription>All trades executed during the backtest</CardDescription>
        </CardHeader>
        <CardContent>
          {trades.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No trades executed
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Symbol</th>
                    <th className="text-left p-2">Side</th>
                    <th className="text-right p-2">Quantity</th>
                    <th className="text-right p-2">Entry</th>
                    <th className="text-right p-2">Exit</th>
                    <th className="text-right p-2">P&L</th>
                    <th className="text-right p-2">P&L %</th>
                    <th className="text-left p-2">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((trade: any) => (
                    <tr key={trade.id} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-medium">{trade.symbol}</td>
                      <td className="p-2">
                        <Badge variant={trade.side === 'buy' ? 'default' : 'destructive'}>
                          {trade.side.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="p-2 text-right">{trade.quantity.toFixed(2)}</td>
                      <td className="p-2 text-right">${trade.entry_price.toFixed(2)}</td>
                      <td className="p-2 text-right">
                        {trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-'}
                      </td>
                      <td className={`p-2 text-right font-medium ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                      </td>
                      <td className={`p-2 text-right ${trade.pnl_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {trade.pnl_pct ? `${trade.pnl_pct.toFixed(2)}%` : '-'}
                      </td>
                      <td className="p-2 text-sm">
                        {new Date(trade.entry_date).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
