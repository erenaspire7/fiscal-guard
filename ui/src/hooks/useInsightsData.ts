import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { env } from "@/config/env";

export interface ReflectionItem {
  decision_id: string;
  item_name: string;
  amount: number;
  created_at: string;
  score: number;
  actual_purchase: boolean | null;
  regret_level: number | null;
  user_feedback: string | null;
}

export interface InsightsData {
  health_score: number;
  impulse_control_growth: number;
  total_capital_retained: number;
  intercepted_count: number;
  correlation_trend: number[];
  reflections: ReflectionItem[];
}

export function useInsightsData() {
  const [data, setData] = useState<InsightsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchInsights = useCallback(async () => {
    if (!token) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${env.apiUrl}/decisions/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch strategic intelligence");
      }

      const stats = await response.json();

      // We'll augment the stats with full decision history for reflections
      const historyRes = await fetch(`${env.apiUrl}/decisions?limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const history = await historyRes.json();

      setData({
        health_score: Math.round(stats.average_score * 10),
        impulse_control_growth: 12, // Placeholder until time-series comparison is in backend
        total_capital_retained: stats.total_requested, // Simplified for now: sum of all intercepted
        intercepted_count: stats.total_decisions,
        correlation_trend: [60, 85, 45, 90, 70, 100, 95, 88], // Placeholder
        reflections: history,
      });
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unknown error occurred",
      );
      console.error("Insights fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  return {
    data,
    isLoading,
    error,
    refresh: fetchInsights,
  };
}
