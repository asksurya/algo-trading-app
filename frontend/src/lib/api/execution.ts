const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ExecutionStatus {
  strategy_id: string;
  is_active: boolean;
  state: string;
  trades_today: number;
  last_signal_at: string | null;
  last_trade_at: string | null;
  error_count: number;
  last_error: string | null;
  // Performance metrics
  total_pnl: number;
  current_pnl: number;
  total_trades: number;
  win_rate: number;
}

export interface Signal {
  id: string;
  strategy_id: string;
  symbol: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  price: number;
  strength: number;
  timestamp: string;
  executed: boolean;
}

export interface PerformanceData {
  total_pnl: number;
  daily_pnl: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface PerformanceMetrics {
  performance: PerformanceData;
}

export async function getExecutionStatus(
  strategyId: string,
  token: string
): Promise<ExecutionStatus> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/status`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch execution status');
  }

  const data = await response.json();
  return data.data;
}

export async function startExecution(
  strategyId: string,
  token: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/start`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to start execution');
  }
}

export async function stopExecution(
  strategyId: string,
  token: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/stop`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to stop execution');
  }
}

export async function resetExecution(
  strategyId: string,
  token: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/reset`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to reset execution');
  }
}

export async function getSignals(
  strategyId: string,
  token: string
): Promise<Signal[]> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/signals`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch signals');
  }

  const data = await response.json();
  return data.data || data;
}

export async function getPerformance(
  strategyId: string,
  token: string
): Promise<PerformanceMetrics> {
  const response = await fetch(
    `${API_URL}/api/v1/strategies/execution/${strategyId}/performance`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch performance');
  }

  const data = await response.json();
  return data.data || data;
}
