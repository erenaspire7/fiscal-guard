import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';

export interface AllocationHealthItem {
  label: string;
  utilized: number;
  limit: number;
  percentage: number;
  status: 'Healthy' | 'Near Capacity' | 'Over Budget';
}

export interface RecentIntercept {
  decision_id: string;
  item_name: string;
  amount: number;
  score: number;
  category: string;
  created_at: string;
}

export interface DashboardData {
  guard_score: number;
  status: string;
  trend: number[];
  allocation_health: AllocationHealthItem[];
  recent_intercepts: RecentIntercept[];
}

export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchDashboardData = useCallback(async () => {
    if (!token) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch dashboard intelligence');
      }

      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error('Dashboard fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  return {
    data,
    isLoading,
    error,
    refresh: fetchDashboardData
  };
}
