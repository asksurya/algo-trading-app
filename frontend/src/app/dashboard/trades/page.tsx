"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { useTrades, useTradingStatistics } from "@/lib/hooks/use-trades";

export default function TradesPage() {
  const { data: trades, isLoading: tradesLoading } = useTrades(0, 100);
  const { data: statistics, isLoading: statsLoading } = useTradingStatistics();

  const formatCurrency = (value: string | number) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(num);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      pending: { variant: "secondary", label: "Pending" },
      filled: { variant: "default", label: "Filled" },
      partially_filled: { variant: "outline", label: "Partially Filled" },
      cancelled: { variant: "destructive", label: "Cancelled" },
      rejected: { variant: "destructive", label: "Rejected" },
    };

    const config = statusConfig[status] || { variant: "secondary" as const, label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Trades</h1>
        <p className="text-muted-foreground">
          View your trading history and statistics
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="text-2xl font-bold">Loading...</div>
            ) : (
              <div className="text-2xl font-bold">{statistics?.total_trades || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="text-2xl font-bold">Loading...</div>
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {statistics?.win_rate.toFixed(1) || 0}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {statistics?.winning_trades || 0} wins / {statistics?.losing_trades || 0} losses
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="text-2xl font-bold">Loading...</div>
            ) : (
              <>
                <div className={`text-2xl font-bold ${
                  statistics && parseFloat(statistics.total_pnl) >= 0 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {statistics ? formatCurrency(statistics.total_pnl) : '$0.00'}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Win/Loss</CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="text-2xl font-bold">Loading...</div>
            ) : (
              <>
                <div className="text-sm">
                  <div className="text-green-600">
                    Win: {statistics?.avg_win ? formatCurrency(statistics.avg_win) : 'N/A'}
                  </div>
                  <div className="text-red-600">
                    Loss: {statistics?.avg_loss ? formatCurrency(statistics.avg_loss) : 'N/A'}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trades List */}
      <Card>
        <CardHeader>
          <CardTitle>Trade History</CardTitle>
          <CardDescription>
            All your executed trades
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tradesLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : trades?.data && trades.data.length > 0 ? (
            <div className="space-y-4" data-testid="trades-table">
              {trades.data.map((trade) => {
                const pnl = trade.realized_pnl ? parseFloat(trade.realized_pnl) : null;
                const isBuy = trade.trade_type === 'buy';
                
                return (
                  <div 
                    key={trade.id} 
                    className="flex items-center justify-between border-b pb-4 last:border-0"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-full ${
                        isBuy ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'
                      }`}>
                        {isBuy ? (
                          <ArrowUpRight className="h-4 w-4 text-green-600" />
                        ) : (
                          <ArrowDownRight className="h-4 w-4 text-red-600" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{trade.ticker}</p>
                          {getStatusBadge(trade.status)}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {trade.trade_type.toUpperCase()} • {trade.filled_quantity || trade.quantity} shares
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(trade.executed_at || trade.created_at)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="font-medium">
                        {trade.filled_avg_price 
                          ? formatCurrency(parseFloat(trade.filled_avg_price))
                          : trade.price 
                            ? formatCurrency(parseFloat(trade.price))
                            : 'Market'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Total: {trade.filled_avg_price 
                          ? formatCurrency(parseFloat(trade.filled_avg_price) * parseFloat(trade.filled_quantity || trade.quantity))
                          : 'Pending'}
                      </p>
                      {pnl !== null && (
                        <p className={`text-sm font-medium ${pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(pnl)}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-12 text-center">
              <p className="text-muted-foreground">No trades yet</p>
              <p className="text-sm text-muted-foreground mt-2">
                Trades will appear here once you execute them
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
