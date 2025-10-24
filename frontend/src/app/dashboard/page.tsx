"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, DollarSign, Activity, BarChart3, RefreshCw } from "lucide-react";
import { useAccount, usePositions, useBrokerOrders } from "@/lib/hooks/use-broker";
import { useStrategies } from "@/lib/hooks/use-strategies";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  // Fetch real Alpaca broker data
  const { data: account, isLoading: accountLoading, refetch: refetchAccount } = useAccount();
  const { data: positions, isLoading: positionsLoading, refetch: refetchPositions } = usePositions();
  const { data: recentOrders, isLoading: ordersLoading } = useBrokerOrders('all', 10);
  const { data: strategies, isLoading: strategiesLoading } = useStrategies(0, 10);

  // Calculate active strategies count
  const activeStrategiesCount = strategies?.filter(s => s.is_active).length || 0;

  // Calculate total unrealized P&L from positions
  const totalUnrealizedPnl = positions?.reduce((sum, pos) => sum + pos.unrealized_pl, 0) || 0;

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Handle refresh
  const handleRefresh = () => {
    refetchAccount();
    refetchPositions();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Live data from Alpaca paper trading account
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          variant="outline"
          size="sm"
          disabled={accountLoading || positionsLoading}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Portfolio Value
            </CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {accountLoading ? (
              <div className="text-2xl font-bold">Loading...</div>
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {account ? formatCurrency(account.portfolio_value) : '$0.00'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Cash: {account ? formatCurrency(account.cash) : '$0.00'}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Buying Power
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {accountLoading ? (
              <div className="text-2xl font-bold">Loading...</div>
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {account ? formatCurrency(account.buying_power) : '$0.00'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {account?.pattern_day_trader ? 'PDT Account' : 'Standard Account'}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Open Positions
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {positionsLoading ? (
              <div className="text-2xl font-bold">Loading...</div>
            ) : (
              <>
                <div className="text-2xl font-bold">{positions?.length || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {account ? formatCurrency(account.long_market_value) : '$0.00'} value
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Unrealized P&L
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {positionsLoading ? (
              <div className="text-2xl font-bold">Loading...</div>
            ) : (
              <>
                <div className={`text-2xl font-bold ${
                  totalUnrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(totalUnrealizedPnl)}
                </div>
                <p className={`text-xs ${totalUnrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {totalUnrealizedPnl >= 0 ? '+' : ''}{((totalUnrealizedPnl / (account?.portfolio_value || 1)) * 100).toFixed(2)}%
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Open Positions</CardTitle>
            <CardDescription>
              Current holdings from Alpaca
            </CardDescription>
          </CardHeader>
          <CardContent>
            {positionsLoading ? (
              <p className="text-sm text-muted-foreground">Loading positions...</p>
            ) : positions && positions.length > 0 ? (
              <div className="space-y-4">
                {positions.slice(0, 5).map((position) => (
                  <div key={position.symbol} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{position.symbol}</p>
                      <p className="text-xs text-muted-foreground">
                        {position.qty} shares @ {formatCurrency(position.avg_entry_price)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {formatCurrency(position.market_value)}
                      </p>
                      <p className={`text-xs ${position.unrealized_pl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(position.unrealized_pl)} ({formatPercentage(position.unrealized_plpc * 100)})
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No open positions</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Orders</CardTitle>
            <CardDescription>
              Latest order activity
            </CardDescription>
          </CardHeader>
          <CardContent>
            {ordersLoading ? (
              <p className="text-sm text-muted-foreground">Loading orders...</p>
            ) : recentOrders && recentOrders.length > 0 ? (
              <div className="space-y-4">
                {recentOrders.slice(0, 5).map((order) => (
                  <div key={order.id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{order.symbol}</p>
                      <p className="text-xs text-muted-foreground">
                        {order.side.toUpperCase()} {order.type} • {order.filled_qty || order.qty || 0} shares
                      </p>
                    </div>
                    <div className="text-right">
                      <span className={`text-xs font-medium ${
                        order.status === 'filled' ? 'text-green-600' :
                        order.status === 'canceled' ? 'text-red-600' :
                        order.status === 'pending_new' ? 'text-yellow-600' :
                        'text-gray-600'
                      }`}>
                        {order.status.replace('_', ' ').toUpperCase()}
                      </span>
                      {order.filled_avg_price && (
                        <p className="text-xs text-muted-foreground">
                          @ {formatCurrency(order.filled_avg_price)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No recent orders</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
