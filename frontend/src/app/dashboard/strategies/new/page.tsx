"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateStrategy } from "@/lib/hooks/use-strategies";
import { Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NewStrategyPage() {
  const router = useRouter();
  const createStrategy = useCreateStrategy();

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    strategy_type: "momentum",
    tickers: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const tickersArray = formData.tickers
      .split(",")
      .map(t => t.trim().toUpperCase())
      .filter(t => t.length > 0);

    createStrategy.mutate(
      {
        name: formData.name,
        description: formData.description || undefined,
        strategy_type: formData.strategy_type,
        parameters: {}, // Basic empty parameters
        tickers: tickersArray.length > 0 ? tickersArray : undefined,
      },
      {
        onSuccess: () => {
          router.push("/dashboard/strategies");
        },
      }
    );
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/strategies">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Create New Strategy</h1>
          <p className="text-muted-foreground">
            Set up a new trading strategy
          </p>
        </div>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Strategy Details</CardTitle>
          <CardDescription>
            Enter the details for your new trading strategy
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Strategy Name *</Label>
              <Input
                id="name"
                name="name"
                placeholder="e.g., My Momentum Strategy"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <textarea
                id="description"
                name="description"
                placeholder="Describe your strategy..."
                value={formData.description}
                onChange={handleChange}
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="strategy_type">Strategy Type *</Label>
              <select
                id="strategy_type"
                name="strategy_type"
                value={formData.strategy_type}
                onChange={handleChange}
                required
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="momentum">Momentum</option>
                <option value="mean_reversion">Mean Reversion</option>
                <option value="macd">MACD</option>
                <option value="rsi">RSI</option>
                <option value="bollinger_bands">Bollinger Bands</option>
                <option value="sma_crossover">SMA Crossover</option>
                <option value="breakout">Breakout</option>
                <option value="vwap">VWAP</option>
                <option value="pairs_trading">Pairs Trading</option>
                <option value="ml_strategy">ML Strategy</option>
                <option value="adaptive_ml">Adaptive ML</option>
              </select>
              <p className="text-xs text-muted-foreground">
                Choose the type of trading strategy to implement
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tickers">Tickers (Optional)</Label>
              <Input
                id="tickers"
                name="tickers"
                placeholder="e.g., AAPL, MSFT, GOOGL"
                value={formData.tickers}
                onChange={handleChange}
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated list of stock tickers to trade with this strategy
              </p>
            </div>

            <div className="flex gap-4">
              <Button
                type="submit"
                disabled={createStrategy.isPending}
                className="flex-1"
              >
                {createStrategy.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Strategy"
                )}
              </Button>
              <Link href="/dashboard/strategies" className="flex-1">
                <Button type="button" variant="outline" className="w-full">
                  Cancel
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
