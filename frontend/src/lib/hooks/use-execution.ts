import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getExecutionStatus,
  startExecution,
  stopExecution,
  resetExecution,
  getSignals,
  getPerformance,
  ExecutionStatus,
  Signal,
  PerformanceMetrics,
} from '../api/execution';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function useExecutionStatus(strategyId: string) {
  const token = getToken();

  return useQuery<ExecutionStatus>({
    queryKey: ['execution', strategyId],
    queryFn: () => getExecutionStatus(strategyId, token!),
    enabled: !!token && !!strategyId,
    refetchInterval: 5000, // Poll every 5 seconds
  });
}

export function useSignals(strategyId: string, _limit?: number) {
  const token = getToken();

  return useQuery<Signal[]>({
    queryKey: ['execution', strategyId, 'signals'],
    queryFn: () => getSignals(strategyId, token!),
    enabled: !!token && !!strategyId,
    refetchInterval: 5000,
  });
}

export function usePerformance(strategyId: string, _days?: number) {
  const token = getToken();

  return useQuery<PerformanceMetrics>({
    queryKey: ['execution', strategyId, 'performance'],
    queryFn: () => getPerformance(strategyId, token!),
    enabled: !!token && !!strategyId,
    refetchInterval: 10000,
  });
}

export function useStartExecution() {
  const queryClient = useQueryClient();
  const token = getToken();

  return useMutation({
    mutationFn: (strategyId: string) => startExecution(strategyId, token!),
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ['execution', strategyId] });
    },
  });
}

export function useStopExecution() {
  const queryClient = useQueryClient();
  const token = getToken();

  return useMutation({
    mutationFn: (strategyId: string) => stopExecution(strategyId, token!),
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ['execution', strategyId] });
    },
  });
}

export function useResetExecution() {
  const queryClient = useQueryClient();
  const token = getToken();

  return useMutation({
    mutationFn: (strategyId: string) => resetExecution(strategyId, token!),
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ['execution', strategyId] });
    },
  });
}
