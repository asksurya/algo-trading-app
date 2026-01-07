'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Rocket, Loader2 } from 'lucide-react';
import LiveTradingAPI from '@/lib/api/live-trading';

interface DeployToLiveButtonProps {
  strategyId: string;
  strategyName: string;
  symbols: string[];
  variant?: 'default' | 'outline' | 'secondary' | 'ghost' | 'link' | 'destructive' | null | undefined;
  size?: 'default' | 'sm' | 'lg' | 'icon' | null | undefined;
  className?: string;
}

export function DeployToLiveButton({
  strategyId,
  strategyName,
  symbols,
  variant = 'default',
  size = 'default',
  className,
}: DeployToLiveButtonProps) {
  const router = useRouter();
  const [deploying, setDeploying] = useState(false);

  const handleDeploy = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      // For now, just log - in production you'd want a toast notification
      console.error('Please log in to deploy strategies');
      router.push('/login');
      return;
    }

    if (symbols.length === 0) {
      console.error('No symbols specified for trading');
      return;
    }

    setDeploying(true);

    try {
      const api = new LiveTradingAPI(token);
      const result = await api.quickDeploy({
        strategy_id: strategyId,
        symbols: symbols,
        name: `Live - ${strategyName}`,
        auto_execute: true,
        check_interval: 300, // 5 minutes
      });

      // Success - redirect to live trading page
      router.push('/dashboard/live-trading');
    } catch (error) {
      console.error('Failed to deploy strategy:', error instanceof Error ? error.message : 'Unknown error');
      // In production, show a toast notification
    } finally {
      setDeploying(false);
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleDeploy}
      disabled={deploying || symbols.length === 0}
      className={className}
    >
      {deploying ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Deploying...
        </>
      ) : (
        <>
          <Rocket className="mr-2 h-4 w-4" />
          Deploy to Live
        </>
      )}
    </Button>
  );
}
