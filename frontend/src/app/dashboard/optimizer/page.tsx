'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Loader2, 
  TrendingUp, 
  TrendingDown, 
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RefreshCw
} from 'lucide-react';
import {
  analyzeStrategies,
  getJobStatus,
  getOptimizationResults,
  executeOptimalStrategies,
  type OptimizeStrategyRequest,
  type OptimizeStrategyResponse,
  type OptimizationResult,
  type ExecuteOptimalResponse,
} from '@/lib/api/optimizer';
import { strategiesApi } from '@/lib/api/strategies';
import type { Strategy } from '@/types';

export default function OptimizerPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state
  const [symbols, setSymbols] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [initialCapital, setInitialCapital] = useState('100000');
  const [maxPositionPct, setMaxPositionPct] = useState('10');

  // Results state
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [results, setResults] = useState<Record<string, OptimizationResult> | null>(null);
  const [executionResults, setExecutionResults] = useState<ExecuteOptimalResponse | null>(null);

  // Strategies
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategies, setSelectedStrategies] = useState<number[]>([]);

  // Load strategies on mount
  useEffect(() => {
    loadStrategies();
    // Set default date range (last year)
    const end = new Date();
    const start = new Date();
    start.setFullYear(end.getFullYear() - 1);
    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
  }, []);

  // Poll job status
  useEffect(() => {
    if (!jobId || !polling) return;

    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId);
        setJobStatus(status.status);
        setProgress(status.progress);
        setCurrentStep(status.current_step || '');

        if (status.status === 'completed' && status.results_available) {
          setPolling(false);
          await loadResults(jobId);
        } else if (status.status === 'failed') {
          setPolling(false);
          setError(status.error_message || 'Optimization failed');
        }
      } catch (err: any) {
        console.error('Error polling status:', err);
        setPolling(false);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, polling]);

  const loadStrategies = async () => {
    try {
      const data = await strategiesApi.list();
      setStrategies(data);
    } catch (err: any) {
      console.error('Error loading strategies:', err);
    }
  };

  const loadResults = async (jid: string) => {
    try {
      const response = await getOptimizationResults(jid);
      setResults(response.results);
      setSuccess('Optimization complete! Review results below.');
    } catch (err: any) {
      setError('Failed to load results: ' + err.message);
    }
  };

  const handleAnalyze = async () => {
    setError(null);
    setSuccess(null);
    setExecutionResults(null);

    // Validate inputs
    const symbolList = symbols.split(',').map(s => s.trim()).filter(s => s);
    if (symbolList.length === 0) {
      setError('Please enter at least one ticker symbol');
      return;
    }
    if (!startDate || !endDate) {
      setError('Please select start and end dates');
      return;
    }

    // Basic date validation
    const start = new Date(startDate);
    const end = new Date(endDate);
    const daysDiff = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysDiff < 1) {
      setError('End date must be after start date');
      return;
    }
    
    // Warning for large requests
    if (daysDiff > 365 || symbolList.length > 5) {
      const numStrategies = selectedStrategies.length > 0 ? selectedStrategies.length : strategies.length;
      const totalBacktests = symbolList.length * numStrategies;
      
      setSuccess(
        `Large analysis requested: ${symbolList.length} symbols, ${daysDiff} days, ${totalBacktests} backtests. ` +
        `This may take several minutes. Data will be fetched in chunks.`
      );
    }

    setLoading(true);

    try {
      const request: OptimizeStrategyRequest = {
        symbols: symbolList,
        strategy_ids: selectedStrategies.length > 0 ? selectedStrategies : undefined,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        initial_capital: parseFloat(initialCapital),
      };

      const response = await analyzeStrategies(request);
      setJobId(response.job_id);
      setJobStatus('pending');
      setPolling(true);
      setSuccess(`Analysis started! Job ID: ${response.job_id}`);
    } catch (err: any) {
      setError('Failed to start analysis: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (symbolsToExecute?: string[]) => {
    if (!jobId) {
      setError('No optimization job found');
      return;
    }

    setExecuting(true);
    setError(null);

    try {
      const response = await executeOptimalStrategies({
        optimization_job_id: jobId,
        symbols: symbolsToExecute,
        auto_size: true,
        max_position_pct: parseFloat(maxPositionPct),
      });

      setExecutionResults(response);
      setSuccess(
        `Executed ${response.total_executed} trades, ` +
        `${response.total_blocked} blocked, ${response.total_failed} failed`
      );
    } catch (err: any) {
      setError('Execution failed: ' + err.message);
    } finally {
      setExecuting(false);
    }
  };

  const getSymbolsList = () => {
    return symbols.split(',').map(s => s.trim()).filter(s => s);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Strategy Optimizer</h1>
        <p className="text-muted-foreground">
          Analyze multiple strategies across multiple tickers and auto-execute the best performers
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Analysis Configuration</CardTitle>
          <CardDescription>
            Enter tickers and configure backtest parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="symbols">Ticker Symbols (comma-separated)</Label>
            <Input
              id="symbols"
              placeholder="AAPL, GOOGL, MSFT, TSLA"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value.toUpperCase())}
              disabled={loading || polling}
            />
            <p className="text-sm text-muted-foreground">
              {getSymbolsList().length} symbol(s) entered
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="startDate">Start Date</Label>
              <Input
                id="startDate"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={loading || polling}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="endDate">End Date</Label>
              <Input
                id="endDate"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={loading || polling}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="capital">Initial Capital ($)</Label>
              <Input
                id="capital"
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(e.target.value)}
                disabled={loading || polling}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="maxPosition">Max Position Size (%)</Label>
              <Input
                id="maxPosition"
                type="number"
                value={maxPositionPct}
                onChange={(e) => setMaxPositionPct(e.target.value)}
                disabled={loading || polling}
                min="1"
                max="100"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Strategies (Leave empty for all)</Label>
            <Select
              onValueChange={(value) => {
                const id = parseInt(value);
                setSelectedStrategies(prev => 
                  prev.includes(id) 
                    ? prev.filter(i => i !== id)
                    : [...prev, id]
                );
              }}
              disabled={loading || polling}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select strategies" />
              </SelectTrigger>
              <SelectContent>
                {strategies.map(strategy => (
                  <SelectItem key={strategy.id} value={String(strategy.id)}>
                    {strategy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedStrategies.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {selectedStrategies.map(id => {
                  const strategy = strategies.find(s => Number(s.id) === id);
                  return strategy ? (
                    <Badge key={id} variant="secondary">
                      {strategy.name}
                      <button
                        className="ml-2"
                        onClick={() => setSelectedStrategies(prev => prev.filter(i => i !== id))}
                      >
                        ×
                      </button>
                    </Badge>
                  ) : null;
                })}
              </div>
            )}
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={loading || polling}
            className="w-full"
          >
            {loading || polling ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {polling ? `Analyzing... ${progress.toFixed(0)}%` : 'Starting...'}
              </>
            ) : (
              <>
                <Activity className="mr-2 h-4 w-4" />
                Analyze Strategies
              </>
            )}
          </Button>

          {polling && currentStep && (
            <p className="text-sm text-center text-muted-foreground">
              {currentStep}
            </p>
          )}
        </CardContent>
      </Card>

      {results && Object.keys(results).length > 0 && (
        <>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Optimization Results</CardTitle>
                <CardDescription>
                  Best performing strategies for each ticker
                </CardDescription>
              </div>
              <Button
                onClick={() => handleExecute()}
                disabled={executing}
                size="lg"
              >
                {executing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Execute All Best Strategies
                  </>
                )}
              </Button>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue={Object.keys(results)[0]} className="w-full">
                <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${Object.keys(results).length}, 1fr)` }}>
                  {Object.keys(results).map(symbol => (
                    <TabsTrigger key={symbol} value={symbol}>
                      {symbol}
                    </TabsTrigger>
                  ))}
                </TabsList>
                {Object.entries(results).map(([symbol, result]) => (
                  <TabsContent key={symbol} value={symbol} className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Best Strategy</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{result.best_strategy.strategy_name}</div>
                          <Badge variant="outline">Rank #{result.best_strategy.rank}</Badge>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Composite Score</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{result.best_strategy.composite_score.toFixed(2)}</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Total Return</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className={`text-2xl font-bold ${result.best_strategy.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {result.best_strategy.total_return >= 0 ? <TrendingUp className="inline h-5 w-5" /> : <TrendingDown className="inline h-5 w-5" />}
                            {result.best_strategy.total_return.toFixed(2)}%
                          </div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Win Rate</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{result.best_strategy.win_rate.toFixed(1)}%</div>
                        </CardContent>
                      </Card>
                    </div>

                    <div className="flex justify-end">
                      <Button
                        onClick={() => handleExecute([symbol])}
                        disabled={executing}
                        variant="outline"
                      >
                        {executing ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="mr-2 h-4 w-4" />
                        )}
                        Execute {symbol} Only
                      </Button>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold mb-2">All Strategy Performance</h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Rank</TableHead>
                            <TableHead>Strategy</TableHead>
                            <TableHead className="text-right">Score</TableHead>
                            <TableHead className="text-right">Return</TableHead>
                            <TableHead className="text-right">Sharpe</TableHead>
                            <TableHead className="text-right">Max DD</TableHead>
                            <TableHead className="text-right">Win Rate</TableHead>
                            <TableHead className="text-right">Trades</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {result.all_performances.map((perf) => (
                            <TableRow key={perf.strategy_id} className={perf.rank === 1 ? 'bg-green-50' : ''}>
                              <TableCell>
                                <Badge variant={perf.rank === 1 ? 'default' : 'outline'}>
                                  #{perf.rank}
                                </Badge>
                              </TableCell>
                              <TableCell className="font-medium">{perf.strategy_name}</TableCell>
                              <TableCell className="text-right font-semibold">{perf.composite_score.toFixed(2)}</TableCell>
                              <TableCell className={`text-right ${perf.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {perf.total_return.toFixed(2)}%
                              </TableCell>
                              <TableCell className="text-right">{perf.sharpe_ratio?.toFixed(2) || 'N/A'}</TableCell>
                              <TableCell className="text-right text-red-600">{perf.max_drawdown.toFixed(2)}%</TableCell>
                              <TableCell className="text-right">{perf.win_rate.toFixed(1)}%</TableCell>
                              <TableCell className="text-right">{perf.total_trades}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </CardContent>
          </Card>

          {executionResults && (
            <Card>
              <CardHeader>
                <CardTitle>Execution Results</CardTitle>
                <CardDescription>
                  {executionResults.total_executed} successful, {executionResults.total_blocked} blocked, {executionResults.total_failed} failed
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {executionResults.successful.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2 flex items-center text-green-600">
                      <CheckCircle2 className="mr-2 h-5 w-5" />
                      Successful ({executionResults.successful.length})
                    </h3>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Symbol</TableHead>
                          <TableHead>Strategy</TableHead>
                          <TableHead className="text-right">Shares</TableHead>
                          <TableHead className="text-right">Value</TableHead>
                          <TableHead className="text-right">Score</TableHead>
                          <TableHead>Order ID</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {executionResults.successful.map((result, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">{result.symbol}</TableCell>
                            <TableCell>{result.strategy}</TableCell>
                            <TableCell className="text-right">{result.shares}</TableCell>
                            <TableCell className="text-right">${result.estimated_value?.toFixed(2)}</TableCell>
                            <TableCell className="text-right">{result.composite_score?.toFixed(2)}</TableCell>
                            <TableCell className="text-sm text-muted-foreground">{result.order_id?.slice(0, 8)}...</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                {executionResults.blocked.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2 flex items-center text-yellow-600">
                      <AlertTriangle className="mr-2 h-5 w-5" />
                      Blocked by Risk Rules ({executionResults.blocked.length})
                    </h3>
                    <div className="space-y-2">
                      {executionResults.blocked.map((result, idx) => (
                        <Alert key={idx} variant="destructive">
                          <AlertDescription>
                            <strong>{result.symbol}</strong> - {result.strategy}
                            <ul className="mt-2 space-y-1">
                              {result.breaches?.map((breach, bidx) => (
                                <li key={bidx} className="text-sm">
                                  • {breach.rule}: {breach.message} ({breach.action})
                                </li>
                              ))}
                            </ul>
                          </AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </div>
                )}

                {executionResults.failed.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-2 flex items-center text-red-600">
                      <XCircle className="mr-2 h-5 w-5" />
                      Failed ({executionResults.failed.length})
                    </h3>
                    <div className="space-y-2">
                      {executionResults.failed.map((result, idx) => (
                        <Alert key={idx} variant="destructive">
                          <AlertDescription>
                            <strong>{result.symbol}</strong>: {result.error}
                          </AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
