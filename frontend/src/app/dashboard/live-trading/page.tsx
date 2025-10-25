'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import LiveTradingAPI, { Dashboard, LiveStrategy, SignalHistory } from '@/lib/api/live-trading';

export default function LiveTradingPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth/login');
      return;
    }
    setToken(token);
    fetchDashboard(token);
    const interval = setInterval(() => fetchDashboard(token), 5000);
    return () => clearInterval(interval);
  }, [router]);

  const fetchDashboard = async (accessToken: string) => {
    try {
      const api = new LiveTradingAPI(accessToken);
      const data = await api.getDashboard();
      setDashboard(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6">Loading...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-600">Error: {error}</div>;
  }

  if (!dashboard) {
    return <div className="p-6">No data available</div>;
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Live Trading Automation</h1>
        <Link href="/dashboard/live-trading/new">
          <Button>Create Strategy</Button>
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-gray-600">Active Strategies</div>
          <div className="text-3xl font-bold">{dashboard.summary.active_strategies}</div>
          <div className="text-xs text-gray-500">of {dashboard.summary.total_strategies}</div>
        </Card>

        <Card className="p-4">
          <div className="text-sm text-gray-600">Signals Today</div>
          <div className="text-3xl font-bold">{dashboard.summary.signals_today}</div>
          <div className="text-xs text-gray-500">Detected</div>
        </Card>

        <Card className="p-4">
          <div className="text-sm text-gray-600">Trades Today</div>
          <div className="text-3xl font-bold">{dashboard.summary.trades_today}</div>
          <div className="text-xs text-gray-500">Executed</div>
        </Card>

        <Card className="p-4">
          <div className="text-sm text-gray-600">Daily P&L</div>
          <div className={`text-3xl font-bold ${dashboard.summary.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${dashboard.summary.daily_pnl.toFixed(2)}
          </div>
          <div className="text-xs text-gray-500">Total: ${dashboard.summary.total_pnl.toFixed(2)}</div>
        </Card>
      </div>

      {/* Active Strategies */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Active Strategies</h2>
        {dashboard.active_strategies.length === 0 ? (
          <p className="text-gray-500">No active strategies. Create one to get started!</p>
        ) : (
          <div className="space-y-4">
            {dashboard.active_strategies.map((strategy) => (
              <StrategyCard key={strategy.id} strategy={strategy} onUpdate={() => token && fetchDashboard(token)} />
            ))}
          </div>
        )}
      </Card>

      {/* Recent Signals */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Recent Signals</h2>
        {dashboard.recent_signals.length === 0 ? (
          <p className="text-gray-500">No signals detected yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Symbol</th>
                  <th className="text-left py-2">Signal</th>
                  <th className="text-left py-2">Price</th>
                  <th className="text-left py-2">Strength</th>
                  <th className="text-left py-2">Status</th>
                  <th className="text-left py-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.recent_signals.slice(0, 10).map((signal) => (
                  <tr key={signal.id} className="border-b hover:bg-gray-50">
                    <td className="py-2 font-mono">{signal.symbol}</td>
                    <td className={`py-2 font-bold ${signal.signal_type === 'BUY' ? 'text-green-600' : signal.signal_type === 'SELL' ? 'text-red-600' : 'text-gray-600'}`}>
                      {signal.signal_type}
                    </td>
                    <td className="py-2">${signal.price.toFixed(2)}</td>
                    <td className="py-2">{((signal.signal_strength || 0) * 100).toFixed(0)}%</td>
                    <td className="py-2">
                      <span className={`px-2 py-1 rounded text-xs ${signal.executed ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {signal.executed ? 'Executed' : 'Pending'}
                      </span>
                    </td>
                    <td className="py-2 text-gray-500">{new Date(signal.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function StrategyCard({
  strategy,
  onUpdate,
}: {
  strategy: LiveStrategy;
  onUpdate: () => void;
}) {
  const [actionLoading, setActionLoading] = useState(false);
  const token = localStorage.getItem('access_token') || '';

  const handleAction = async (action: 'start' | 'stop' | 'pause') => {
    setActionLoading(true);
    try {
      const api = new LiveTradingAPI(token);
      if (action === 'start') {
        await api.startStrategy(strategy.id);
      } else if (action === 'stop') {
        await api.stopStrategy(strategy.id);
      } else {
        await api.pauseStrategy(strategy.id);
      }
      onUpdate?.();
    } catch (err) {
      console.error(`Failed to ${action} strategy:`, err);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="border rounded-lg p-4 hover:bg-gray-50">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-bold text-lg">{strategy.name}</h3>
          <p className="text-sm text-gray-600">
            Monitoring {strategy.symbols.length} symbols • Check interval: {strategy.check_interval}s
          </p>
        </div>
        <div className="flex gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            strategy.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
            strategy.status === 'PAUSED' ? 'bg-yellow-100 text-yellow-800' :
            strategy.status === 'ERROR' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {strategy.status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-3 text-sm">
        <div>
          <div className="text-gray-600">Signals</div>
          <div className="font-bold">{strategy.total_signals}</div>
        </div>
        <div>
          <div className="text-gray-600">Trades</div>
          <div className="font-bold">{strategy.executed_trades}</div>
        </div>
        <div>
          <div className="text-gray-600">Positions</div>
          <div className="font-bold">{strategy.current_positions}</div>
        </div>
        <div>
          <div className="text-gray-600">P&L</div>
          <div className={`font-bold ${strategy.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${strategy.daily_pnl.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        {strategy.status === 'ACTIVE' ? (
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction('pause')}
              disabled={actionLoading}
            >
              Pause
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleAction('stop')}
              disabled={actionLoading}
            >
              Stop
            </Button>
          </>
        ) : strategy.status === 'STOPPED' ? (
          <Button
            size="sm"
            onClick={() => handleAction('start')}
            disabled={actionLoading}
          >
            Start
          </Button>
        ) : (
          <Button
            size="sm"
            onClick={() => handleAction('start')}
            disabled={actionLoading}
          >
            Resume
          </Button>
        )}
        <Link href={`/dashboard/live-trading/${strategy.id}`}>
          <Button variant="outline" size="sm">
            Details
          </Button>
        </Link>
      </div>

      {strategy.error_message && (
        <div className="mt-2 p-2 bg-red-100 border border-red-200 rounded text-sm text-red-800">
          Error: {strategy.error_message}
        </div>
      )}
    </div>
  );
}
