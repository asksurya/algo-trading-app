import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getExecutionStatus, startExecution, stopExecution, ExecutionStatus } from '../api/execution';

export function useExecutionStatus(strategyId: string) {
  const token = typeof window !== 'undefined'
    ? localStorage.getItem('access_token')
    : null;

  return useQuery<ExecutionStatus>({
    queryKey: ['execution', strategyId],
    queryFn: () => getExecutionStatus(strategyId, token!),
    enabled: !!token && !!strategyId,
    refetchInterval: 5000, // Poll every 5 seconds
  });
}

export function useStartExecution() {
  const queryClient = useQueryClient();
  const token = typeof window !== 'undefined'
    ? localStorage.getItem('access_token')
    : null;

  return useMutation({
    mutationFn: (strategyId: string) => startExecution(strategyId, token!),
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ['execution', strategyId] });
    },
  });
}

export function useStopExecution() {
  const queryClient = useQueryClient();
  const token = typeof window !== 'undefined'
    ? localStorage.getItem('access_token')
    : null;

  return useMutation({
    mutationFn: (strategyId: string) => stopExecution(strategyId, token!),
    onSuccess: (_, strategyId) => {
      queryClient.invalidateQueries({ queryKey: ['execution', strategyId] });
    },
  });
}
