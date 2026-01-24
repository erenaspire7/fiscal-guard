import { useState, useMemo } from "react";
import { useInsightsData } from "@/hooks/useInsightsData";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import {
  Zap,
  Calendar,
  Smile,
  Frown,
  Meh,
  CheckCircle2,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";
import { env } from "@/config/env";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

type TimeWindow = "30day" | "all";

export default function Insights() {
  const [timeWindow, setTimeWindow] = useState<TimeWindow>("30day");

  const startDate = useMemo(() => {
    if (timeWindow === "30day") {
      const date = new Date();
      date.setDate(date.getDate() - 30);
      return date;
    }
    return null;
  }, [timeWindow]);

  const itemsPerPage = 5;
  const { token } = useAuth();
  const [submittingFeedback, setSubmittingFeedback] = useState<string | null>(
    null,
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [editingFeedback, setEditingFeedback] = useState<string | null>(null);
  const [feedbackText, setFeedbackText] = useState("");

  const offset = (currentPage - 1) * itemsPerPage;
  const { data, isLoading, refresh } = useInsightsData({
    startDate,
    limit: itemsPerPage,
    offset,
  });

  const paginatedReflections = data?.reflections || [];
  const totalItems = data?.total_reflections || 0;
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  // Reset to page 1 when time window changes
  const handleTimeWindowChange = (window: TimeWindow) => {
    setTimeWindow(window);
    setCurrentPage(1);
  };

  const handleFeedback = async (
    decisionId: string,
    actualPurchase: boolean,
    regretLevel: number,
  ) => {
    if (!token || submittingFeedback) return;

    setSubmittingFeedback(decisionId);
    try {
      const response = await fetch(
        `${env.apiUrl}/decisions/${decisionId}/feedback`,
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

  const handleUpdateFeedback = async (
    decisionId: string,
    actualPurchase: boolean,
    regretLevel: number,
    feedback: string,
  ) => {
    if (!token || submittingFeedback) return;

    setSubmittingFeedback(decisionId);
    try {
      const response = await fetch(
        `${env.apiUrl}/decisions/${decisionId}/feedback`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            actual_purchase: actualPurchase,
            regret_level: regretLevel,
            feedback: feedback || null,
          }),
        },
      );

      if (response.ok) {
        setEditingFeedback(null);
        setFeedbackText("");
        refresh();
      }
    } catch (error) {
      console.error("Failed to update feedback:", error);
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
            <button
              onClick={() => handleTimeWindowChange("30day")}
              className={cn(
                "px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors",
                timeWindow === "30day"
                  ? "bg-[#10b981] text-[#020403] hover:bg-[#10b981]/90"
                  : "text-muted-foreground hover:text-white",
              )}
            >
              30-Day Window
            </button>
            <button
              onClick={() => handleTimeWindowChange("all")}
              className={cn(
                "px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors",
                timeWindow === "all"
                  ? "bg-[#10b981] text-[#020403] hover:bg-[#10b981]/90"
                  : "text-muted-foreground hover:text-white",
              )}
            >
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
            {paginatedReflections.map((item) => (
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

                  {editingFeedback === item.decision_id ? (
                    <div className="mt-4 md:mt-0 w-full space-y-2">
                      <textarea
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value)}
                        placeholder="Add your reflection..."
                        className="w-full bg-[#0F1A16] border border-white/10 rounded-lg p-2 text-sm text-white placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50 resize-none"
                        rows={3}
                      />
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => {
                            setEditingFeedback(null);
                            setFeedbackText("");
                          }}
                          className="px-3 py-1 text-xs text-muted-foreground hover:text-white transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() =>
                            handleUpdateFeedback(
                              item.decision_id,
                              item.actual_purchase ?? true,
                              item.regret_level ?? 5,
                              feedbackText,
                            )
                          }
                          disabled={submittingFeedback === item.decision_id}
                          className="px-3 py-1 text-xs bg-primary text-[#020403] rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
                        >
                          Save
                        </button>
                      </div>
                    </div>
                  ) : item.user_feedback ? (
                    <div className="mt-4 md:mt-0 pl-4 border-l-2 border-primary/30 w-full group/feedback">
                      <p className="text-sm italic text-muted-foreground/80">
                        "{item.user_feedback}"
                      </p>
                      <button
                        onClick={() => {
                          setEditingFeedback(item.decision_id);
                          setFeedbackText(item.user_feedback || "");
                        }}
                        className="mt-2 text-[10px] text-primary/60 hover:text-primary transition-colors opacity-0 group-hover/feedback:opacity-100"
                      >
                        Edit
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        setEditingFeedback(item.decision_id);
                        setFeedbackText("");
                      }}
                      className="hidden md:block text-xs italic text-muted-foreground opacity-30 hover:opacity-60 hover:text-primary transition-all mt-auto text-left"
                    >
                      + Add reflection...
                    </button>
                  )}
                </div>
              </div>
            ))}
            {paginatedReflections.length === 0 && !isLoading && (
              <p className="text-center text-muted-foreground text-sm py-10">
                No reflections found
                {timeWindow === "30day"
                  ? " in the last 30 days"
                  : " in your history"}
                .
              </p>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pt-6">
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious
                        onClick={() =>
                          setCurrentPage((p) => Math.max(1, p - 1))
                        }
                        className={cn(
                          "cursor-pointer bg-[#0A1210] border border-white/5 text-white hover:bg-[#0F1A16] hover:text-primary",
                          currentPage === 1 && "opacity-50 cursor-not-allowed",
                        )}
                      />
                    </PaginationItem>

                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                      (page) => {
                        // Show first page, last page, current page, and pages around current
                        if (
                          page === 1 ||
                          page === totalPages ||
                          (page >= currentPage - 1 && page <= currentPage + 1)
                        ) {
                          return (
                            <PaginationItem key={page}>
                              <PaginationLink
                                onClick={() => setCurrentPage(page)}
                                isActive={currentPage === page}
                                className={cn(
                                  "cursor-pointer bg-[#0A1210] border border-white/5 text-white hover:bg-[#0F1A16] hover:text-primary",
                                  currentPage === page &&
                                    "bg-primary/20 text-primary border-primary/20",
                                )}
                              >
                                {page}
                              </PaginationLink>
                            </PaginationItem>
                          );
                        } else if (
                          page === currentPage - 2 ||
                          page === currentPage + 2
                        ) {
                          return (
                            <PaginationItem key={page}>
                              <PaginationEllipsis className="text-muted-foreground" />
                            </PaginationItem>
                          );
                        }
                        return null;
                      },
                    )}

                    <PaginationItem>
                      <PaginationNext
                        onClick={() =>
                          setCurrentPage((p) => Math.min(totalPages, p + 1))
                        }
                        className={cn(
                          "cursor-pointer bg-[#0A1210] border border-white/5 text-white hover:bg-[#0F1A16] hover:text-primary",
                          currentPage === totalPages &&
                            "opacity-50 cursor-not-allowed",
                        )}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
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
                <div className="flex items-center justify-center gap-2 mb-2">
                  <h3 className="text-xl font-bold text-white">
                    Peace of Mind Score
                  </h3>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button className="text-muted-foreground hover:text-primary transition-colors">
                          <HelpCircle className="w-4 h-4" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs bg-[#0F1A16] border-white/10 text-white p-4">
                        <p className="text-xs leading-relaxed">
                          <span className="font-bold text-primary">
                            How it's calculated:
                          </span>
                          <br />
                          Your score is based on the average AI risk assessment
                          of your purchase decisions. Higher scores indicate
                          better financial discipline and lower impulsive buying
                          tendencies. The score considers factors like budget
                          alignment, necessity, and emotional purchase triggers.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
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
                  ${data?.total_capital_retained.toLocaleString() || "0"}
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
