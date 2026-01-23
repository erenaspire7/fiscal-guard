import { useState } from "react";
import { useInsightsData } from "@/hooks/useInsightsData";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import { Zap, Calendar, Smile, Frown, Meh, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";

export default function Insights() {
  const { data, isLoading, refresh } = useInsightsData();
  const { token } = useAuth();
  const [submittingFeedback, setSubmittingFeedback] = useState<string | null>(
    null,
  );

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
    <div
      className={cn(
        "min-h-screen text-foreground font-sans pb-32 md:pb-0 md:pl-64 transition-all duration-300",
        ThemeBackgrounds[DEFAULT_THEME],
      )}
    >
      <Sidebar />

      <main className="px-6 py-8 md:p-12 max-w-7xl mx-auto space-y-8">
        {/* Desktop Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="md:hidden">
            <p className="text-[10px] font-bold uppercase tracking-wider text-primary opacity-80">
              Regret Tracker
            </p>
            <h1 className="text-3xl font-bold tracking-tight">Insights</h1>
          </div>
          <h2 className="hidden md:block text-3xl font-bold tracking-tight text-white">
            Reflections
          </h2>

          <div className="flex items-center gap-2 self-end md:self-auto">
            <button className="bg-[#10b981] text-[#020403] px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-[#10b981]/90 transition-colors">
              30-Day Window
            </button>
            <button className="text-muted-foreground hover:text-white px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-colors">
              All Time
            </button>
            <button className="w-9 h-9 bg-card/10 rounded-lg flex items-center justify-center border border-white/5 hover:bg-white/10 transition-colors">
              <Calendar className="w-4 h-4 text-primary" />
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Reflections List */}
          <div className="lg:col-span-2 space-y-4 order-2 lg:order-1">
            {data?.reflections.map((item) => (
              <div
                key={item.decision_id}
                className="bg-[#0A1210] border border-white/5 p-6 md:p-8 rounded-[32px] flex flex-col md:flex-row gap-6 md:gap-8 hover:bg-[#0F1A16] transition-colors group"
              >
                <div className="flex-1 space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-xl font-bold text-white mb-1">
                        {item.item_name}
                      </h4>
                      <p className="text-xs text-primary font-medium tracking-wide">
                        Analyzed{" "}
                        {new Date(item.created_at).toLocaleDateString()}{" "}
                        <span className="text-muted-foreground">•</span> $
                        {item.amount.toLocaleString()}
                      </p>
                    </div>
                    <span
                      className={cn(
                        "md:hidden text-[8px] font-black px-2 py-1 rounded-md tracking-tighter",
                        item.score >= 7
                          ? "bg-primary/20 text-primary"
                          : "bg-orange-500/20 text-orange-400",
                      )}
                    >
                      AI: {item.score >= 7 ? "LOW RISK" : "HIGH RISK"}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-50">
                      {item.regret_level === null
                        ? "Rate Satisfaction"
                        : "Satisfaction"}
                    </p>
                    <div className="flex gap-3">
                      {[
                        { val: 2, Icon: Smile, colorClass: "text-primary" },
                        { val: 5, Icon: Smile, colorClass: "text-primary" },
                        { val: 7, Icon: Meh, colorClass: "text-primary" },
                        { val: 8, Icon: Meh, colorClass: "text-orange-400" },
                        { val: 10, Icon: Frown, colorClass: "text-orange-400" },
                      ].map(({ val, Icon, colorClass }) => (
                        <button
                          key={val}
                          onClick={() =>
                            handleFeedback(
                              item.decision_id,
                              item.actual_purchase ?? true,
                              val,
                            )
                          }
                          disabled={submittingFeedback === item.decision_id}
                          className="focus:outline-none hover:scale-110 transition-transform disabled:opacity-50"
                        >
                          <Icon
                            className={cn(
                              "w-5 h-5 transition-colors",
                              item.regret_level !== null &&
                                ((item.regret_level <= 3 && val <= 3) ||
                                  (item.regret_level > 3 &&
                                    item.regret_level <= 5 &&
                                    val === 5) ||
                                  (item.regret_level > 5 &&
                                    item.regret_level <= 7 &&
                                    val === 7) ||
                                  (item.regret_level > 7 &&
                                    item.regret_level < 9 &&
                                    val === 8) ||
                                  (item.regret_level >= 9 && val === 10))
                                ? colorClass
                                : "text-muted-foreground opacity-20 hover:opacity-60",
                            )}
                          />
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Desktop Right Side of Card */}
                <div className="flex flex-col items-end justify-between min-w-[140px]">
                  <span
                    className={cn(
                      "hidden md:inline-flex text-[10px] font-black px-3 py-1.5 rounded-lg tracking-widest border border-white/5",
                      item.score >= 7
                        ? "bg-primary/10 text-primary border-primary/20"
                        : "bg-orange-500/10 text-orange-400 border-orange-500/20",
                    )}
                  >
                    AI: {item.score >= 7 ? "LOW RISK" : "HIGH RISK"}
                  </span>

                  {item.user_feedback ? (
                    <div className="mt-4 md:mt-0 pl-4 border-l-2 border-primary/30 w-full">
                      <p className="text-sm italic text-muted-foreground/80">
                        "{item.user_feedback}"
                      </p>
                    </div>
                  ) : (
                    <p className="hidden md:block text-xs italic text-muted-foreground opacity-30 mt-auto">
                      No reflection added yet...
                    </p>
                  )}
                </div>
              </div>
            ))}
            {(!data || data.reflections.length === 0) && !isLoading && (
              <p className="text-center text-muted-foreground text-sm py-10">
                No reflections found in your history.
              </p>
            )}
          </div>

          {/* Right Column: Stats Widgets */}
          <div className="space-y-6 order-1 lg:order-2">
            {/* Financial Health Gauge */}
            <div className="bg-[#0A1210] border border-white/5 rounded-[40px] p-8 flex flex-col items-center justify-center text-center relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-32 bg-primary/5 blur-3xl rounded-full translate-y-[-50%]" />
              <div className="relative w-48 h-48 mb-6">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="44"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="6"
                    className="text-white/5"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="44"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="6"
                    strokeDasharray="276"
                    strokeDashoffset={
                      276 - (276 * (data?.health_score || 0)) / 100
                    }
                    strokeLinecap="round"
                    className="text-primary shadow-[0_0_15px_rgba(16,185,129,0.5)] transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-6xl font-black tracking-tighter text-white">
                    {data?.health_score || (isLoading ? ".." : "0")}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 mb-2">
                  Financial Health
                </p>
                <h3 className="text-xl font-bold text-white mb-2">
                  Peace of Mind Score
                </h3>
                <p className="text-primary text-xs font-bold">
                  Your impulse control grew {data?.impulse_control_growth || 0}%
                  this month.
                </p>
              </div>
            </div>

            {/* Total Capital Retained */}
            <div className="bg-[#0A1210] border border-white/5 rounded-[40px] p-8 flex items-center justify-between relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="space-y-2 relative z-10">
                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60">
                  Total Capital Retained
                </p>
                <h3 className="text-4xl font-black text-primary drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]">
                  ${data?.total_capital_retained.toLocaleString() || "0,000"}
                </h3>
                <p className="text-xs text-muted-foreground font-medium max-w-[150px]">
                  Saved from{" "}
                  <span className="text-white font-bold">
                    {data?.intercepted_count || 0} impulsive
                  </span>{" "}
                  buy attempts.
                </p>
              </div>
              <div className="w-12 h-12 bg-[#0F2922] rounded-full flex items-center justify-center text-primary shadow-[0_0_15px_rgba(16,185,129,0.3)] relative z-10">
                <Zap className="w-6 h-6" fill="currentColor" />
              </div>
            </div>

            {/* Insight Summary */}
            <div className="bg-[#0A1210] border border-white/5 rounded-[40px] p-8">
              <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 mb-4">
                Insight Summary
              </p>
              <p className="text-sm text-muted-foreground leading-relaxed mb-8">
                Your financial guardian has intercepted several high-risk
                purchases recently. By maintaining this level of discipline, you
                are on track to reach your savings goals{" "}
                <span className="text-primary font-bold">15% faster</span>.
              </p>

              <div className="bg-[#0F1A16] rounded-2xl p-4 flex items-center justify-between border border-white/5">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                <span className="text-xs font-bold text-white">
                  Growth Correlation
                </span>
                <CheckCircle2 className="w-5 h-5 text-primary" />
              </div>
            </div>
          </div>
        </div>
      </main>

      <div className="md:hidden">
        <Navbar />
      </div>
    </div>
  );
}
