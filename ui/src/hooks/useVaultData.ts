import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';

export interface BudgetCategory {
  limit: number;
  spent: number;
}

export interface Budget {
  budget_id: string;
  name: string;
  total_monthly: number;
  period_start: string;
  period_end: string;
  categories: Record<string, BudgetCategory>;
}

export interface Goal {
  goal_id: string;
  goal_name: string;
  target_amount: number;
  current_amount: number;
  priority: 'high' | 'medium' | 'low';
  deadline: string | null;
  is_completed: boolean;
}

export function useVaultData() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchData = useCallback(async () => {
    if (!token) return;

    setIsLoading(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const [budgetsRes, goalsRes] = await Promise.all([
        fetch(`${baseUrl}/budgets`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${baseUrl}/goals`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (!budgetsRes.ok || !goalsRes.ok) {
        throw new Error('Failed to fetch vault data');
      }

      const budgetsData = await budgetsRes.json();
      const goalsData = await goalsRes.json();

      setBudgets(budgetsData);
      setGoals(goalsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error('Vault fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    budgets,
    goals,
    isLoading,
    error,
    refresh: fetchData
  };
}
