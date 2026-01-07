"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, TrendingUp, TrendingDown, Loader2, Trash2 } from "lucide-react";
import { useStrategies, useDeleteStrategy, useUpdateStrategy } from "@/lib/hooks/use-strategies";
import { useCurrentPositions } from "@/lib/hooks/use-trades";
import { Badge } from "@/components/ui/badge";
import { DeployToLiveButton } from "@/components/deploy-to-live-button";

export default function StrategiesPage() {
  const { data: strategies, isLoading } = useStrategies();
  const { data: positions } = useCurrentPositions();
  const deleteStrategy = useDeleteStrategy();
  const updateStrategy = useUpdateStrategy();

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete "${name}"?`)) {
      deleteStrategy.mutate(id);
    }
  };

  const handleToggleActive = async (id: string, currentStatus: boolean) => {
    updateStrategy.mutate({
      id,
      data: { is_active: !currentStatus },
    });
  };

  const getStrategyPositions = (strategyId: string) => {
    return positions?.filter(p => p.strategy_id === strategyId) || [];
  };

  const calculateStrategyPnL = (strategyId: string) => {
    const strategyPositions = getStrategyPositions(strategyId);
    const totalPnL = strategyPositions.reduce((sum, position) => {
      const unrealizedPnL = position.unrealized_pnl ? parseFloat(position.unrealized_pnl) : 0;
      const realizedPnL = position.realized_pnl ? parseFloat(position.realized_pnl) : 0;
      return sum + unrealizedPnL + realizedPnL;
    }, 0);
    return totalPnL;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Strategies</h1>
          <p className="text-muted-foreground">
            Manage your trading strategies
          </p>
        </div>
        <Link href="/dashboard/strategies/new">
          <Button data-testid="create-strategy-button">
            <Plus className="mr-2 h-4 w-4" />
            New Strategy
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : strategies && strategies.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" data-testid="strategies-table">
          {strategies.map((strategy) => {
            const strategyPositions = getStrategyPositions(strategy.id);
            const pnl = calculateStrategyPnL(strategy.id);
            const totalValue = strategyPositions.reduce((sum, pos) => {
              const value = pos.current_price && pos.quantity
                ? parseFloat(pos.current_price) * parseFloat(pos.quantity)
                : 0;
              return sum + value;
            }, 0);
            const pnlPercentage = totalValue > 0 ? (pnl / totalValue) * 100 : 0;

            return (
              <Card key={strategy.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      {strategy.name}
                      {pnl !== 0 && (
                        pnl >= 0 ? (
                          <TrendingUp className="h-5 w-5 text-green-600" />
                        ) : (
                          <TrendingDown className="h-5 w-5 text-red-600" />
                        )
                      )}
                    </CardTitle>
                  </div>
                  <CardDescription>
                    {strategy.description || strategy.strategy_type}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Status:</span>
                      <Badge 
                        variant={strategy.is_active ? "default" : "secondary"}
                        className="cursor-pointer"
                        onClick={() => handleToggleActive(strategy.id, strategy.is_active)}
                      >
                        {strategy.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Positions:</span>
                      <span className="font-medium">{strategyPositions.length}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Value:</span>
                      <span className="font-medium">{formatCurrency(totalValue)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">P&L:</span>
                      <span className={`font-medium ${pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(pnl)} ({formatPercentage(pnlPercentage)})
                      </span>
                    </div>
                    {strategy.is_backtested && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Backtested:</span>
                        <Badge variant="outline">Yes</Badge>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-2 mt-4">
                    <div className="flex gap-2">
                      <Link href={`/dashboard/strategies/${strategy.id}`} className="flex-1">
                        <Button className="w-full" variant="outline">
                          View Details
                        </Button>
                      </Link>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => handleDelete(strategy.id, strategy.name)}
                        disabled={deleteStrategy.isPending}
                      >
                        {deleteStrategy.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4 text-red-600" />
                        )}
                      </Button>
                    </div>
                    <DeployToLiveButton
                      strategyId={strategy.id}
                      strategyName={strategy.name}
                      symbols={['AAPL']}
                      variant="default"
                      size="default"
                      className="w-full"
                    />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">No strategies yet</p>
            <Link href="/dashboard/strategies/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Strategy
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
