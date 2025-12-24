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
