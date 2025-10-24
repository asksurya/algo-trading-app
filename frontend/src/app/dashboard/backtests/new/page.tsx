'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateBacktest } from '@/lib/hooks/use-backtests';
import { useStrategies } from '@/lib/hooks/use-strategies';

export default function NewBacktestPage() {
  const router = useRouter();
  const { data: strategiesData } = useStrategies();
  const createMutation = useCreateBacktest();

  const [formData, setFormData] = useState({
    strategy_id: '',
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    initial_capital: '100000',
    commission: '0.001',
    slippage: '0.0005',
  });

  const strategies = strategiesData || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Convert dates to ISO format
    const startDate = new Date(formData.start_date).toISOString();
    const endDate = new Date(formData.end_date).toISOString();

    await createMutation.mutateAsync({
      strategy_id: formData.strategy_id,
      name: formData.name,
      description: formData.description || undefined,
      start_date: startDate,
      end_date: endDate,
      initial_capital: parseFloat(formData.initial_capital),
      commission: parseFloat(formData.commission),
      slippage: parseFloat(formData.slippage),
    });

    router.push('/dashboard/backtests');
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Create Backtest</h1>
        <p className="text-muted-foreground">
          Test your strategy on historical market data
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Backtest Configuration</CardTitle>
          <CardDescription>
            Configure the parameters for your backtest
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Strategy Selection */}
            <div className="space-y-2">
              <Label htmlFor="strategy_id">Strategy *</Label>
              <select
                id="strategy_id"
                name="strategy_id"
                value={formData.strategy_id}
                onChange={handleChange}
                required
                className="w-full h-10 px-3 rounded-md border border-input bg-background"
              >
                <option value="">Select a strategy</option>
                {strategies.map((strategy: any) => (
                  <option key={strategy.id} value={strategy.id}>
                    {strategy.name} ({strategy.strategy_type})
                  </option>
                ))}
              </select>
            </div>

            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Backtest Name *</Label>
              <Input
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Q1 2024 Backtest"
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Testing RSI strategy on tech stocks"
              />
            </div>

            {/* Date Range */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date *</Label>
                <Input
                  id="start_date"
                  name="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end_date">End Date *</Label>
                <Input
                  id="end_date"
                  name="end_date"
                  type="date"
                  value={formData.end_date}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            {/* Financial Parameters */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Financial Parameters</h3>
              
              <div className="space-y-2">
                <Label htmlFor="initial_capital">Initial Capital ($) *</Label>
                <Input
                  id="initial_capital"
                  name="initial_capital"
                  type="number"
                  step="1000"
                  value={formData.initial_capital}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="commission">Commission Rate *</Label>
                  <Input
                    id="commission"
                    name="commission"
                    type="number"
                    step="0.0001"
                    value={formData.commission}
                    onChange={handleChange}
                    placeholder="0.001 (0.1%)"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Default: 0.001 (0.1%)
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="slippage">Slippage Rate *</Label>
                  <Input
                    id="slippage"
                    name="slippage"
                    type="number"
                    step="0.0001"
                    value={formData.slippage}
                    onChange={handleChange}
                    placeholder="0.0005 (0.05%)"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Default: 0.0005 (0.05%)
                  </p>
                </div>
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending}
                className="flex-1"
              >
                {createMutation.isPending ? 'Creating...' : 'Run Backtest'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
