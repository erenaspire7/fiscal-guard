import { useMemo, useState } from "react";
import { useInsightsData } from "@/hooks/useInsightsData";
import { useAuth } from "@/contexts/AuthContext";
import { AreaChart, Area, Tooltip, ResponsiveContainer } from "recharts";
import Navbar from "@/components/Navbar";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Zap,
  Calendar,
  Leaf,
  Smile,
  Frown,
  Meh,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function Insights() {
  const { data, isLoading, refresh } = useInsightsData();
  const { token } = useAuth();
  const [submittingFeedback, setSubmittingFeedback] = useState<string | null>(
    null,
  );

  const chartData = useMemo(() => {
    return (data?.correlation_trend || [60, 85, 45, 90, 70, 100, 95, 88]).map(
      (val, i) => ({
        name: i + 1,
        score: val,
      }),
    );
  }, [data]);

  const handleFeedback = async (
    decisionId: string,
    actualPurchase: boolean,
    regretLevel: number,
  ) => {
    if (!token || submittingFeedback) return;

    setSubmittingFeedback(decisionId);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/decisions/${decisionId}/feedback`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            actual_purchase: actualPurchase,
            regret_level: regretLevel,
            feedback: null,
          }),
        },
      );

      if (response.ok) {
        refresh();
      }
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    } finally {
      setSubmittingFeedback(null);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans pb-32">
      {/* Header */}
      <header className="px-6 py-8 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-primary opacity-80">
            Regret Tracker
          </p>
          <h1 className="text-3xl font-bold tracking-tight">Insights</h1>
        </div>
        <div className="flex gap-2">
          <button className="w-10 h-10 bg-card/50 rounded-full flex items-center justify-center border border-white/5">
            <Calendar className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </header>

      <main className="px-6 space-y-8">
        {/* Peace of Mind Score - Circular Gauge */}
        <div className="flex flex-col items-center justify-center py-6 text-center space-y-4">
          <div className="relative w-48 h-48">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="44"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                className="text-card/50 opacity-20"
              />
              <circle
                cx="50"
                cy="50"
                r="44"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                strokeDasharray="276"
                strokeDashoffset={276 - (276 * (data?.health_score || 0)) / 100}
                strokeLinecap="round"
                className="text-primary shadow-primary-glow transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-5xl font-black tracking-tighter">
                {data?.health_score || (isLoading ? ".." : "0")}
              </span>
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                Financial Health
              </p>
            </div>
            <div className="absolute top-2 right-2 text-primary opacity-20">
              <Leaf className="w-8 h-8" fill="currentColor" />
            </div>
          </div>
          <div>
            <h2 className="text-xl font-bold">Peace of Mind Score</h2>
            <p className="text-primary text-xs font-bold mt-1 text-glow">
              Your impulse control grew {data?.impulse_control_growth || 0}%
              this month.
            </p>
          </div>
        </div>

        {/* Impact Stats - Retained Capital */}
        <Card className="bg-card/50 border-none shadow-xl rounded-[32px] overflow-hidden group active:scale-[0.98] transition-transform">
          <CardContent className="p-7 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-50">
                Total Capital Retained
              </p>
              <h3 className="text-3xl font-black text-primary text-glow">
                ${data?.total_capital_retained.toLocaleString() || "0.00"}
              </h3>
              <p className="text-xs text-muted-foreground font-medium">
                Saved from{" "}
                <span className="text-foreground font-bold">
                  {data?.intercepted_count || 0} impulsive
                </span>{" "}
                buy attempts.
              </p>
            </div>
            <div className="w-14 h-14 bg-primary/20 rounded-2xl flex items-center justify-center text-primary shadow-primary-glow">
              <Zap className="w-7 h-7" fill="currentColor" />
            </div>
          </CardContent>
        </Card>

        {/* AI Growth Correlation Chart */}
        <section className="space-y-4">
          <h3 className="text-xl font-bold tracking-tight px-1 flex items-center gap-2">
            AI Growth Correlation{" "}
            <CheckCircle2 className="w-4 h-4 text-primary opacity-40" />
          </h3>
          <div className="bg-card/40 p-6 rounded-[32px] h-48 overflow-hidden">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(10, 20, 15, 0.9)",
                    border: "1px solid rgba(16, 185, 129, 0.2)",
                    borderRadius: "16px",
                    color: "#fff",
                    fontSize: "12px",
                    fontWeight: "bold",
                  }}
                  itemStyle={{ color: "#10b981" }}
                  labelStyle={{ display: "none" }}
                  cursor={{ stroke: "#10b981", strokeWidth: 1, opacity: 0.2 }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#10b981"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorScore)"
                  animationDuration={2000}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Refined Reflections - High Density */}
        <section className="space-y-4">
          <div className="flex justify-between items-end px-1">
            <h3 className="text-xl font-bold tracking-tight">Reflections</h3>
            <span className="text-[10px] font-bold text-primary uppercase tracking-widest opacity-60">
              30-Day Window
            </span>
          </div>
          <div className="space-y-3">
            {data?.reflections.map((item) => (
              <div
                key={item.decision_id}
                className="bg-card/50 p-5 rounded-[28px] space-y-4"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-sm">{item.item_name}</h4>
                    <p className="text-[10px] text-muted-foreground font-medium">
                      Analyzed {new Date(item.created_at).toLocaleDateString()}{" "}
                      • ${item.amount.toLocaleString()}
                    </p>
                  </div>
                  <span
                    className={cn(
                      "text-[8px] font-black px-2 py-1 rounded-md tracking-tighter",
                      item.score >= 7
                        ? "bg-primary/20 text-primary"
                        : "bg-orange-500/20 text-orange-400",
                    )}
                  >
                    AI: {item.score >= 7 ? "LOW RISK" : "HIGH RISK"}
                  </span>
                </div>

                <div className="flex items-center justify-between border-t border-white/5 pt-3">
                  <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest opacity-50">
                    {item.regret_level === null
                      ? "Rate Satisfaction"
                      : "Satisfaction"}
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() =>
                        handleFeedback(
                          item.decision_id,
                          item.actual_purchase ?? true,
                          2,
                        )
                      }
                      disabled={submittingFeedback === item.decision_id}
                      className="focus:outline-none hover:scale-110 transition-transform disabled:opacity-50"
                    >
                      <Smile
                        className={cn(
                          "w-4 h-4 transition-colors",
                          item.regret_level !== null && item.regret_level <= 3
                            ? "text-primary"
                            : "text-muted-foreground opacity-20 hover:opacity-60",
                        )}
                      />
                    </button>
                    <button
                      onClick={() =>
                        handleFeedback(
                          item.decision_id,
                          item.actual_purchase ?? true,
                          5,
                        )
                      }
                      disabled={submittingFeedback === item.decision_id}
                      className="focus:outline-none hover:scale-110 transition-transform disabled:opacity-50"
                    >
                      <Smile
                        className={cn(
                          "w-4 h-4 transition-colors",
                          item.regret_level !== null &&
                            item.regret_level > 3 &&
                            item.regret_level <= 5
                            ? "text-primary"
                            : "text-muted-foreground opacity-20 hover:opacity-60",
                        )}
                      />
                    </button>
                    <button
                      onClick={() =>
                        handleFeedback(
                          item.decision_id,
                          item.actual_purchase ?? true,
                          7,
                        )
                      }
                      disabled={submittingFeedback === item.decision_id}
                      className="focus:outline-none hover:scale-110 transition-transform disabled:opacity-50"
                    >
                      <Meh
                        className={cn(
                          "w-4 h-4 transition-colors",
                          item.regret_level !== null &&
                            item.regret_level > 5 &&
                            item.regret_level <= 7
                            ? "text-primary"
                            : "text-muted-foreground opacity-20 hover:opacity-60",
                        )}
                      />
                    </button>
                    <button
                      onClick={() =>
                        handleFeedback(
                          item.decision_id,
                          item.actual_purchase ?? true,
                          8,
                        )
                      }
                      disabled={submittingFeedback === item.decision_id}
                      className="focus:outline-none hover:scale-110 transition-transform disabled:opacity-50"
                    >
                      <Meh
                        className={cn(
                          "w-4 h-4 transition-colors",
                          item.regret_level !== null &&
                            item.regret_level > 7 &&
                            item.regret_level < 9
                            ? "text-orange-400"
                            : "text-muted-foreground opacity-20 hover:opacity-60",
                        )}
                      />
                    </button>
                    <button
                      onClick={() =>
                        handleFeedback(
                          item.decision_id,
                          item.actual_purchase ?? true,
                          10,
                        )
                      }
                      disabled={submittingFeedback === item.decision_id}
                      className="focus:outline-none hover:scale-110 transition-transform disabled:opacity-50"
                    >
                      <Frown
                        className={cn(
                          "w-4 h-4 transition-colors",
                          item.regret_level !== null && item.regret_level >= 9
                            ? "text-orange-400"
                            : "text-muted-foreground opacity-20 hover:opacity-60",
                        )}
                      />
                    </button>
                  </div>
                </div>

                {item.user_feedback && (
                  <p className="text-[11px] italic text-muted-foreground/70 bg-background/40 p-3 rounded-xl border-l-2 border-primary/30">
                    "{item.user_feedback}"
                  </p>
                )}
              </div>
            ))}
            {(!data || data.reflections.length === 0) && !isLoading && (
              <p className="text-center text-muted-foreground text-sm py-10">
                No reflections found in your history.
              </p>
            )}
          </div>
        </section>
      </main>

      <Navbar />
    </div>
  );
}
