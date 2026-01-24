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
  total_reflections: number;
}

export function useInsightsData(
  options: { limit?: number; offset?: number; startDate?: Date | null } = {},
) {
  const { limit = 10, offset = 0, startDate = null } = options;
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
      const params = new URLSearchParams();
      params.append("limit", limit.toString());
      params.append("offset", offset.toString());

      if (startDate) {
        params.append("start_date", startDate.toISOString());
      }

      const historyRes = await fetch(`${env.apiUrl}/decisions?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const historyData = await historyRes.json();

      setData({
        health_score: Math.round(stats.average_score * 10),
        impulse_control_growth: stats.impulse_control_growth || 0,
        total_capital_retained: stats.capital_retained || 0,
        intercepted_count: stats.intercepted_count || 0,
        correlation_trend: stats.weekly_scores || [],
        reflections: historyData.items,
        total_reflections: historyData.total,
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
  }, [token, limit, offset, startDate]);

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
