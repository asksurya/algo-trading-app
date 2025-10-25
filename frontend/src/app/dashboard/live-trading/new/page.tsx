'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import LiveTradingAPI, { LiveStrategyCreate } from '@/lib/api/live-trading';

export default function NewLiveStrategyPage() {
  const router = useRouter();
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const [formData, setFormData] = useState<LiveStrategyCreate>({
    name: '',
    strategy_id: 0,
    symbols: [],
    check_interval: 300,
    auto_execute: false,
    max_positions: 5,
    daily_loss_limit: undefined,
    position_size_pct: 0.02,
  });

  const [symbolInput, setSymbolInput] = useState('');

  useEffect(() => {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      router.push('/auth/login');
      return;
    }

    setToken(accessToken);
    fetchStrategies(accessToken);
  }, [router]);

  const fetchStrategies = async (accessToken: string) => {
    try {
      const api = new LiveTradingAPI(accessToken);
      // Fetch available strategies from /api/v1/strategies
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/strategies`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await response.json();
      setStrategies(data);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategies');
      setLoading(false);
    }
  };

  const handleAddSymbol = () => {
    if (symbolInput.trim() && !formData.symbols.includes(symbolInput.toUpperCase())) {
      setFormData({
        ...formData,
        symbols: [...formData.symbols, symbolInput.toUpperCase()],
      });
      setSymbolInput('');
    }
  };

  const handleRemoveSymbol = (symbol: string) => {
    setFormData({
      ...formData,
      symbols: formData.symbols.filter((s) => s !== symbol),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      if (!token) throw new Error('No auth token');
      if (!formData.name.trim()) throw new Error('Name is required');
      if (!formData.strategy_id) throw new Error('Strategy is required');
      if (formData.symbols.length === 0) throw new Error('At least one symbol is required');

      const api = new LiveTradingAPI(token);
      const result = await api.createStrategy(formData);

      router.push(`/dashboard/live-trading/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create strategy');
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Create Live Trading Strategy</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-300 rounded text-red-800">
          {error}
        </div>
      )}

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium mb-2">Strategy Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., My Automated RSI Strategy"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Strategy Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">Base Strategy</label>
            <select
              value={formData.strategy_id}
              onChange={(e) => setFormData({ ...formData, strategy_id: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Select a strategy...</option>
              {strategies.map((strategy: any) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.name}
                </option>
              ))}
            </select>
          </div>

          {/* Symbols */}
          <div>
            <label className="block text-sm font-medium mb-2">Symbols to Monitor</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={symbolInput}
                onChange={(e) => setSymbolInput(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSymbol())}
                placeholder="e.g., AAPL, MSFT"
                className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <Button type="button" onClick={handleAddSymbol}>
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.symbols.map((symbol) => (
                <div key={symbol} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full flex items-center gap-2">
                  {symbol}
                  <button
                    type="button"
                    onClick={() => handleRemoveSymbol(symbol)}
                    className="text-blue-600 hover:text-blue-900 font-bold"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Check Interval */}
          <div>
            <label className="block text-sm font-medium mb-2">Check Interval (seconds)</label>
            <select
              value={formData.check_interval}
              onChange={(e) => setFormData({ ...formData, check_interval: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={60}>1 minute</option>
              <option value={300}>5 minutes</option>
              <option value={900}>15 minutes</option>
              <option value={1800}>30 minutes</option>
              <option value={3600}>1 hour</option>
            </select>
          </div>

          {/* Risk Parameters */}
          <div className="border-t pt-6">
            <h3 className="font-bold mb-4">Risk Parameters</h3>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-2">Max Position Size ($)</label>
                <input
                  type="number"
                  value={formData.max_position_size || ''}
                  onChange={(e) => setFormData({ ...formData, max_position_size: e.target.value ? parseFloat(e.target.value) : undefined })}
                  placeholder="e.g., 1000"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Max Positions</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={formData.max_positions}
                  onChange={(e) => setFormData({ ...formData, max_positions: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Daily Loss Limit ($)</label>
                <input
                  type="number"
                  value={formData.daily_loss_limit || ''}
                  onChange={(e) => setFormData({ ...formData, daily_loss_limit: e.target.value ? parseFloat(e.target.value) : undefined })}
                  placeholder="e.g., 500"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Position Size (% of Portfolio)</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="0.1"
                    max="50"
                    step="0.1"
                    value={formData.position_size_pct * 100}
                    onChange={(e) => setFormData({ ...formData, position_size_pct: parseFloat(e.target.value) / 100 })}
                    className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-gray-600">%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Auto Execute */}
          <div className="border-t pt-6">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.auto_execute}
                onChange={(e) => setFormData({ ...formData, auto_execute: e.target.checked })}
                className="w-4 h-4"
              />
              <span className="text-sm font-medium">Auto-Execute Trades</span>
            </label>
            <p className="text-sm text-gray-600 mt-2">
              {formData.auto_execute
                ? 'Trades will be executed automatically when signals are detected.'
                : 'Signals will be detected but not executed. You can execute manually.'}
            </p>
          </div>

          {/* Buttons */}
          <div className="flex gap-4 pt-6 border-t">
            <Button
              type="submit"
              disabled={submitting || !formData.strategy_id || formData.symbols.length === 0}
              className="flex-1"
            >
              {submitting ? 'Creating...' : 'Create Strategy'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </Card>

      {/* Info Box */}
      <Card className="p-4 mt-6 bg-blue-50 border-blue-200">
        <h4 className="font-bold text-blue-900 mb-2">Tips for Configuration</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Start with a longer check interval (5-15 min) to reduce false signals</li>
          <li>• Set auto-execute to false initially to verify signals</li>
          <li>• Position size % controls risk exposure per trade</li>
          <li>• Daily loss limit helps protect your account from large drawdowns</li>
        </ul>
      </Card>
    </div>
  );
}
