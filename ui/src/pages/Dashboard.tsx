import { useState, useMemo } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useInsightsData } from "@/hooks/useInsightsData";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import { Card, CardContent } from "@/components/ui/card";
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
import {
  Shield,
  Wallet,
  Utensils,
  Film,
  ShoppingBag,
  ShoppingCart,
  Info,
  Zap,
  Calendar,
  Smile,
  Frown,
  Meh,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";
import { env } from "@/config/env";

type TimeWindow = "30day" | "all";

export default function Dashboard() {
  const { user, token } = useAuth();
  const { data: dashboardData, isLoading: dashboardLoading } =
    useDashboardData();

  // Reflections state
  const [timeWindow, setTimeWindow] = useState<TimeWindow>("30day");
  const [submittingFeedback, setSubmittingFeedback] = useState<string | null>(
    null,
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [editingFeedback, setEditingFeedback] = useState<string | null>(null);
  const [feedbackText, setFeedbackText] = useState("");

  const itemsPerPage = 4;

  const startDate = useMemo(() => {
    if (timeWindow === "30day") {
      const date = new Date();
      date.setDate(date.getDate() - 30);
      return date;
    }
    return null;
  }, [timeWindow]);

  const offset = (currentPage - 1) * itemsPerPage;
  const {
    data: insightsData,
    isLoading: insightsLoading,
    refresh,
  } = useInsightsData({
    startDate,
    limit: itemsPerPage,
    offset,
  });

  // Generate chart data or use defaults
  const sparklineData = useMemo(() => {
    if (!dashboardData?.trend || dashboardData.trend.length === 0) {
      const defaults = [4, 7, 5, 8, 6, 9, 7, 8];
      return defaults.map((val, i) => ({
        date: `Day ${i + 1}`,
        score: val,
        item: "Estimated",
      }));
    }

    return dashboardData.trend.map((item, i) => {
      const it = item as any;
      const score = typeof it === "number" ? it : it.score;
      const name = typeof it === "object" ? it.item_name : "Decision";
      const date = typeof it === "object" ? it.date : `Day ${i + 1}`;

      return {
        index: i,
        date: date,
        score: score,
        item: name,
      };
    });
  }, [dashboardData]);

  // Calculate trend velocity
  const trendAnalysis = useMemo(() => {
    if (sparklineData.length < 2) {
      return { velocity: "stable", avgChange: 0, direction: "neutral" };
    }

    let totalChange = 0;
    for (let i = 1; i < sparklineData.length; i++) {
      totalChange += sparklineData[i].score - sparklineData[i - 1].score;
    }
    const avgChange = totalChange / (sparklineData.length - 1);

    if (avgChange > 0.3) {
      return { velocity: "improving", avgChange, direction: "up" };
    } else if (avgChange < -0.3) {
      return { velocity: "declining", avgChange, direction: "down" };
    }
    return { velocity: "stable", avgChange, direction: "neutral" };
  }, [sparklineData]);

  // Helper to get category icon
  const getCategoryIcon = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes("shopping")) return <ShoppingBag className="w-4 h-4" />;
    if (l.includes("dining") || l.includes("food"))
      return <Utensils className="w-4 h-4" />;
    if (l.includes("entertainment") || l.includes("movie"))
      return <Film className="w-4 h-4" />;
    if (l.includes("grocer")) return <ShoppingCart className="w-4 h-4" />;
    return <Wallet className="w-4 h-4" />;
  };

  // Pagination
  const paginatedReflections = insightsData?.reflections || [];
  const totalItems = insightsData?.total_reflections || 0;
  const totalPages = Math.ceil(totalItems / itemsPerPage);

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

      <main className="px-6 py-8 md:p-12 max-w-7xl mx-auto">
        {/* Two-column layout: left content + right reflections */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-8">
          {/* Left Column */}
          <div className="space-y-8">
            {/* Header */}
            <header className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <img
                    src={
                      user?.picture ||
                      `https://api.dicebear.com/7.x/notionists-neutral/svg?seed=${user?.name || "User"}`
                    }
                    alt="Profile"
                    className="w-12 h-12 rounded-full border border-white/10 shadow-lg object-cover"
                  />
                  <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-500 rounded-full border-[3px] border-[#020804] flex items-center justify-center">
                    <Shield className="w-2.5 h-2.5 text-[#020804] fill-current" />
                  </div>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white leading-tight">
                    {user?.name || "Welcome Back"}
                  </h1>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse" />
                    <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-500 opacity-90">
                      Guard Active
                    </p>
                  </div>
                </div>
              </div>
            </header>

            {/* Hero Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Guard Score */}
              <Card className="bg-[#040d07] border border-white/5 shadow-2xl rounded-[24px] relative overflow-hidden">
                <div className="absolute top-0 right-0 p-32 bg-emerald-500/5 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2" />
                <CardContent className="p-6 relative">
                  <div className="flex items-center gap-2 mb-4">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                      Guard Score
                    </p>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info className="w-3 h-3 text-gray-500 hover:text-emerald-500 transition-colors" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="max-w-[200px] text-xs">
                            Your financial discipline score based on spending
                            behavior.
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>

                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-5xl font-black tracking-tighter text-emerald-500 drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                      {dashboardData?.guard_score ||
                        (dashboardLoading ? "..." : "0")}
                    </span>
                    <span className="text-xl font-bold text-gray-500">
                      / 100
                    </span>
                  </div>

                  <div>
                    <span
                      className={cn(
                        "inline-block font-bold text-sm px-2 py-1 rounded-md border",
                        trendAnalysis.avgChange >= 0
                          ? "text-emerald-500 border-emerald-500/20 bg-emerald-500/10"
                          : "text-red-400 border-red-400/20 bg-red-400/5",
                      )}
                    >
                      {trendAnalysis.avgChange > 0 ? "+" : ""}
                      {Math.round(trendAnalysis.avgChange * 10)}%
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Capital Retained */}
              <Card className="bg-[#040d07] border border-white/5 shadow-2xl rounded-[24px] relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <CardContent className="p-6 relative z-10 flex items-center justify-between">
                  <div className="space-y-2">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                      Capital Retained
                    </p>
                    <h3 className="text-3xl font-black text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]">
                      $
                      {insightsData?.total_capital_retained.toLocaleString() ||
                        "0"}
                    </h3>
                    <p className="text-xs text-gray-500 font-medium">
                      So Far
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-500">
                    <Zap className="w-6 h-6" fill="currentColor" />
                  </div>
                </CardContent>
              </Card>

              {/* Intercepts */}
              <Card className="bg-[#040d07] border border-white/5 shadow-2xl rounded-[24px] relative overflow-hidden">
                <CardContent className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                      Intercepts
                    </p>
                  </div>

                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-5xl font-black tracking-tighter text-white">
                      {insightsData?.intercepted_count || "0"}
                    </span>
                  </div>

                  <p className="text-xs text-gray-500 font-medium">
                    Purchases paused for review (all time)
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Budget Health */}
            <Card className="bg-[#040d07] border border-white/5 shadow-2xl rounded-[24px]">
              <CardContent className="p-5">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wide">
                    Budget Health
                  </h3>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
                  {dashboardData?.allocation_health.map((item, idx) => {
                    const statusColor =
                      item.status === "Over Budget"
                        ? "text-red-500"
                        : item.status === "Near Capacity"
                          ? "text-yellow-400"
                          : "text-gray-400";

                    const progressColor =
                      item.status === "Over Budget"
                        ? "bg-red-500"
                        : item.status === "Near Capacity"
                          ? "bg-yellow-400"
                          : "bg-emerald-500";

                    const statusText =
                      item.status === "Over Budget"
                        ? "OVER BUDGET"
                        : item.status === "Near Capacity"
                          ? "NEAR CAPACITY"
                          : "HEALTHY";

                    return (
                      <div key={idx} className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div
                              className={cn(
                                "p-1 rounded-md border border-white/5 bg-emerald-500/10",
                                item.status === "Over Budget"
                                  ? "text-red-500"
                                  : "text-emerald-500",
                              )}
                            >
                              {getCategoryIcon(item.label)}
                            </div>
                            <span className="font-bold text-white text-xs">
                              {item.label}
                            </span>
                          </div>
                          <span
                            className={cn(
                              "text-[8px] font-black uppercase tracking-wider",
                              statusColor,
                            )}
                          >
                            {statusText}
                          </span>
                        </div>

                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full transition-all duration-1000",
                              progressColor,
                            )}
                            style={{
                              width: `${Math.min(100, item.percentage)}%`,
                            }}
                          />
                        </div>

                        <div className="flex justify-between items-center text-[9px] text-muted-foreground/40">
                          <span>
                            <span className="font-bold text-white">
                              ${item.utilized}
                            </span>{" "}
                            / ${item.limit}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                  {(!dashboardData ||
                    dashboardData.allocation_health.length === 0) &&
                    !dashboardLoading && (
                      <div className="col-span-full flex flex-col items-center justify-center text-muted-foreground opacity-50 space-y-2 min-h-50">
                        <Wallet className="w-8 h-8" />
                        <span className="text-xs uppercase tracking-widest">
                          No allocations set
                        </span>
                      </div>
                    )}
                </div>
              </CardContent>
            </Card>

            {/* Growth Analysis Chart */}
            <Card className="bg-[#040d07] border border-white/5 shadow-2xl rounded-[24px] overflow-hidden flex flex-col">
              <CardContent className="p-8 flex-1 flex flex-col">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                        Decision Quality Over Time
                      </p>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <h2 className="text-xl font-bold text-white">
                        Status:{" "}
                        <span
                          className={cn(
                            dashboardData?.status === "Thriving"
                              ? "text-emerald-500"
                              : "text-red-400",
                          )}
                        >
                          {dashboardData?.status ||
                            (dashboardLoading ? "..." : "At Risk")}
                        </span>
                      </h2>
                    </div>
                    <p className="text-emerald-500 text-xs font-medium mt-1 italic opacity-80">
                      {dashboardData?.trend.length || 0} checkpoints active •{" "}
                      {trendAnalysis.velocity === "improving"
                        ? "Decision quality improving"
                        : trendAnalysis.velocity === "declining"
                          ? "Decision quality declining"
                          : "Decision quality stable"}
                    </p>
                  </div>
                  <div className="bg-[#020804] border border-white/5 px-3 py-1.5 rounded-lg text-[10px] font-bold">
                    <span className="text-emerald-500 uppercase">
                      Last 7 Decisions
                    </span>
                  </div>
                </div>

                <div className="w-full h-[150px] mt-4 relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={sparklineData}
                      margin={{ top: 10, right: 80, left: 10, bottom: 10 }}
                    >
                      <defs>
                        <linearGradient
                          id="scoreGradient"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#10b981"
                            stopOpacity={1}
                          />
                          <stop
                            offset="50%"
                            stopColor="#fbbf24"
                            stopOpacity={1}
                          />
                          <stop
                            offset="100%"
                            stopColor="#ef4444"
                            stopOpacity={1}
                          />
                        </linearGradient>
                        <linearGradient
                          id="fillGradient"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#10b981"
                            stopOpacity={0.1}
                          />
                          <stop
                            offset="50%"
                            stopColor="#fbbf24"
                            stopOpacity={0.05}
                          />
                          <stop
                            offset="100%"
                            stopColor="#ef4444"
                            stopOpacity={0.02}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        vertical={false}
                        strokeDasharray="3 3"
                        stroke="rgba(255,255,255,0.05)"
                      />
                      <XAxis
                        dataKey="index"
                        tick={{ fill: "#52525b", fontSize: 9 }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => {
                          const item = sparklineData[value];
                          if (!item) return "";
                          const name = item.item;
                          return name.length > 10
                            ? name.substring(0, 10) + "…"
                            : name;
                        }}
                        interval={0}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis
                        tick={{ fill: "#52525b", fontSize: 10 }}
                        tickLine={false}
                        axisLine={false}
                        domain={[0, 10]}
                        ticks={[0, 4, 7, 10]}
                        width={35}
                      />
                      <ReferenceLine
                        y={7}
                        stroke="#10b981"
                        strokeDasharray="3 3"
                        strokeOpacity={0.5}
                        label={{
                          value: "Safe Threshold",
                          position: "right",
                          fill: "#10b981",
                          fontSize: 9,
                          fontWeight: "bold",
                        }}
                      />
                      <ReferenceLine
                        y={4}
                        stroke="#fbbf24"
                        strokeDasharray="3 3"
                        strokeOpacity={0.3}
                      />
                      <RechartsTooltip
                        cursor={{
                          stroke: "#ffffff",
                          strokeWidth: 1,
                          strokeDasharray: "3 3",
                          opacity: 0.2,
                        }}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const score = Number(payload[0].value);
                            const colorClass =
                              score >= 7
                                ? "text-emerald-500"
                                : score >= 4
                                  ? "text-yellow-400"
                                  : "text-red-400";
                            const riskLabel =
                              score >= 7
                                ? "Low Risk"
                                : score >= 4
                                  ? "Moderate Risk"
                                  : "High Risk";
                            return (
                              <div className="bg-[#040d07]/90 backdrop-blur-md border border-white/10 p-4 rounded-xl shadow-2xl">
                                <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-2 font-bold">
                                  {payload[0].payload.date}
                                </p>
                                <div className="space-y-1">
                                  <p className="text-white font-bold text-sm">
                                    {payload[0].payload.item}
                                  </p>
                                  <div className="flex items-center gap-2">
                                    <span
                                      className={cn(
                                        "text-2xl font-black tracking-tighter",
                                        colorClass,
                                      )}
                                    >
                                      {score}
                                    </span>
                                    <span className="text-[10px] uppercase font-bold text-muted-foreground/60 mt-1">
                                      / 10
                                    </span>
                                  </div>
                                  <p
                                    className={cn(
                                      "text-[10px] font-bold uppercase tracking-wider",
                                      colorClass,
                                    )}
                                  >
                                    {riskLabel}
                                  </p>
                                </div>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="score"
                        stroke="url(#scoreGradient)"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        fill="url(#fillGradient)"
                        animationDuration={1500}
                        dot={({ cx, cy, payload, index }) => {
                          const score = payload.score;
                          const color =
                            score >= 7
                              ? "#10b981"
                              : score >= 4
                                ? "#fbbf24"
                                : "#ef4444";
                          return (
                            <circle
                              key={`dot-${index}`}
                              cx={cx}
                              cy={cy}
                              r={5}
                              fill={color}
                              stroke="#040d07"
                              strokeWidth={2}
                            />
                          );
                        }}
                        activeDot={{
                          r: 7,
                          fill: "#040d07",
                          stroke: "#10b981",
                          strokeWidth: 3,
                        }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Legend */}
                <div className="flex items-center justify-center gap-6 mt-2 pt-2 border-t border-white/5">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-emerald-500" />
                    <span className="text-[9px] font-bold uppercase tracking-wider text-gray-500">
                      Low Risk (7-10)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-yellow-400" />
                    <span className="text-[9px] font-bold uppercase tracking-wider text-gray-500">
                      Moderate (4-6)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="text-[9px] font-bold uppercase tracking-wider text-gray-500">
                      High Risk (0-3)
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Reflections */}
          <div className="space-y-6">
            {/* Reflections Header */}
            <div className="flex flex-col gap-4">
              <h2 className="text-2xl font-bold tracking-tight text-white">
                Purchase Reflections
              </h2>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleTimeWindowChange("30day")}
                  className={cn(
                    "px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors",
                    timeWindow === "30day"
                      ? "bg-emerald-500 text-[#020804] hover:bg-emerald-400"
                      : "text-gray-400 hover:text-white",
                  )}
                >
                  30-Day
                </button>
                <button
                  onClick={() => handleTimeWindowChange("all")}
                  className={cn(
                    "px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors",
                    timeWindow === "all"
                      ? "bg-emerald-500 text-[#020804] hover:bg-emerald-400"
                      : "text-gray-400 hover:text-white",
                  )}
                >
                  All Time
                </button>
              </div>
            </div>

            {/* Reflections List */}
            <div className="space-y-4">
              {paginatedReflections.map((item) => (
                <div
                  key={item.decision_id}
                  className="bg-[#040d07] border border-white/5 p-6 rounded-[24px] flex flex-col gap-4 hover:border-emerald-500/20 hover:shadow-emerald-900/10 transition-all shadow-lg group"
                >
                  <div className="space-y-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-lg font-bold text-white">
                          {item.item_name}
                        </h4>
                        <p className="text-xs text-emerald-500 font-medium">
                          {new Date(item.created_at).toLocaleDateString()} • $
                          {item.amount.toLocaleString()}
                        </p>
                      </div>
                      <span
                        className={cn(
                          "text-[8px] font-black px-2 py-1 rounded-md tracking-tighter border",
                          item.score >= 7
                            ? "bg-emerald-500/20 text-emerald-500 border-emerald-500/20"
                            : "bg-orange-500/20 text-orange-400 border-orange-500/20",
                        )}
                      >
                        AI: {item.score >= 7 ? "LOW RISK" : "HIGH RISK"}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest opacity-50">
                        {item.regret_level === null
                          ? "Rate Satisfaction"
                          : "Satisfaction"}
                      </p>
                      <div className="flex gap-2">
                        {[
                          {
                            val: 2,
                            Icon: Smile,
                            colorClass: "text-emerald-500",
                          },
                          {
                            val: 5,
                            Icon: Smile,
                            colorClass: "text-emerald-500",
                          },
                          { val: 7, Icon: Meh, colorClass: "text-emerald-500" },
                          { val: 8, Icon: Meh, colorClass: "text-orange-400" },
                          {
                            val: 10,
                            Icon: Frown,
                            colorClass: "text-orange-400",
                          },
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
                                "w-4 h-4 transition-colors",
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
                                  : "text-gray-500 opacity-20 hover:opacity-60",
                              )}
                            />
                          </button>
                        ))}
                      </div>
                    </div>

                    {editingFeedback === item.decision_id ? (
                      <div className="mt-2 space-y-2">
                        <textarea
                          value={feedbackText}
                          onChange={(e) => setFeedbackText(e.target.value)}
                          placeholder="Add your reflection..."
                          className="w-full bg-[#020804] border border-white/10 rounded-lg p-2 text-sm text-white placeholder:text-gray-500/50 focus:outline-none focus:border-emerald-500/50 resize-none"
                          rows={2}
                        />
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => {
                              setEditingFeedback(null);
                              setFeedbackText("");
                            }}
                            className="px-3 py-1 text-xs text-gray-500 hover:text-white transition-colors"
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
                            className="px-3 py-1 text-xs bg-emerald-600 text-white rounded-md hover:bg-emerald-500 transition-colors disabled:opacity-50"
                          >
                            Save
                          </button>
                        </div>
                      </div>
                    ) : item.user_feedback ? (
                      <div className="mt-2 pl-3 border-l-2 border-emerald-500/30 group/feedback">
                        <p className="text-xs italic text-gray-500/80">
                          "{item.user_feedback}"
                        </p>
                        <button
                          onClick={() => {
                            setEditingFeedback(item.decision_id);
                            setFeedbackText(item.user_feedback || "");
                          }}
                          className="mt-1 text-[10px] font-bold text-emerald-500/70 hover:text-emerald-500 transition-colors"
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
                        className="text-xs font-bold text-emerald-500/70 hover:text-emerald-500 transition-colors mt-2"
                      >
                        + Add reflection...
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {paginatedReflections.length === 0 && !insightsLoading && (
                <p className="text-center text-gray-500 text-sm py-10">
                  No reflections found
                  {timeWindow === "30day"
                    ? " in the last 30 days"
                    : " in your history"}
                  .
                </p>
              )}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pt-2">
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious
                        onClick={() =>
                          setCurrentPage((p) => Math.max(1, p - 1))
                        }
                        className={cn(
                          "cursor-pointer bg-[#040d07] border border-white/5 text-white hover:bg-emerald-500/10 hover:text-emerald-500",
                          currentPage === 1 && "opacity-50 cursor-not-allowed",
                        )}
                      />
                    </PaginationItem>

                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                      (page) => {
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
                                  "cursor-pointer bg-[#040d07] border border-white/5 text-white hover:bg-emerald-500/10 hover:text-emerald-500",
                                  currentPage === page &&
                                    "bg-emerald-500/20 text-emerald-500 border-emerald-500/20",
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
                              <PaginationEllipsis className="text-gray-500" />
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
                          "cursor-pointer bg-[#040d07] border border-white/5 text-white hover:bg-emerald-500/10 hover:text-emerald-500",
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
        </div>
      </main>

      <div className="md:hidden">
        <Navbar />
      </div>
    </div>
  );
}
