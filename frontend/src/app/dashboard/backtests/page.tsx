'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useBacktests, useDeleteBacktest } from '@/lib/hooks/use-backtests';
import { Plus, TrendingUp, TrendingDown, Trash2 } from 'lucide-react';

export default function BacktestsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useBacktests(page, 20);
  const deleteMutation = useDeleteBacktest();

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this backtest?')) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-96">Loading...</div>;
  }

  const backtests = data?.data || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Backtests</h1>
          <p className="text-muted-foreground">
            Test your strategies on historical data
          </p>
        </div>
        <Link href="/dashboard/backtests/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Backtest
          </Button>
        </Link>
      </div>

      {/* Backtests List */}
      {backtests.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground mb-4">No backtests yet</p>
            <Link href="/dashboard/backtests/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Backtest
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {backtests.map((backtest: any) => (
            <Card key={backtest.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl">{backtest.name}</CardTitle>
                    <CardDescription className="mt-2">
                      {new Date(backtest.start_date).toLocaleDateString()} -{' '}
                      {new Date(backtest.end_date).toLocaleDateString()}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
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
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4 mb-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Initial Capital</div>
                    <div className="text-lg font-semibold">
                      ${backtest.initial_capital.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Total Return</div>
                    <div
                      className={`text-lg font-semibold flex items-center gap-1 ${
                        backtest.total_return && backtest.total_return >= 0
                          ? 'text-green-500'
                          : 'text-red-500'
                      }`}
                    >
                      {backtest.total_return !== null ? (
                        <>
                          {backtest.total_return >= 0 ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <TrendingDown className="h-4 w-4" />
                          )}
                          {backtest.total_return.toFixed(2)}%
                        </>
                      ) : (
                        '-'
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Total Trades</div>
                    <div className="text-lg font-semibold">
                      {backtest.total_trades || '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Win Rate</div>
                    <div className="text-lg font-semibold">
                      {backtest.win_rate !== null
                        ? `${backtest.win_rate.toFixed(1)}%`
                        : '-'}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link href={`/dashboard/backtests/${backtest.id}`} className="flex-1">
                    <Button variant="outline" className="w-full">
                      View Results
                    </Button>
                  </Link>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(backtest.id)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
