import { useMemo } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useDashboardData } from "@/hooks/useDashboardData";
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
  Shield,
  Wallet,
  Utensils,
  Film,
  ShoppingBag,
  ShoppingCart,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";

export default function Dashboard() {
  const { user } = useAuth();
  const { data, isLoading } = useDashboardData();

  // Generate chart data or use defaults
  const sparklineData = useMemo(() => {
    if (!data?.trend || data.trend.length === 0) {
      const defaults = [4, 7, 5, 8, 6, 9, 7, 8];
      return defaults.map((val, i) => ({
        date: `Day ${i + 1}`,
        score: val,
        item: "Estimated",
      }));
    }

    return data.trend.map((item, i) => {
      const it = item as any;
      const score = typeof it === "number" ? it : it.score;
      const name = typeof it === "object" ? it.item_name : "Decision";
      const date = typeof it === "object" ? it.date : `Day ${i + 1}`;

      return {
        index: i, // Unique identifier for each entry
        date: date,
        score: score,
        item: name,
      };
    });
  }, [data]);

  // Calculate trend velocity (average change between consecutive scores)
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

  return (
    <div
      className={cn(
        "min-h-screen text-foreground font-sans pb-32 md:pb-0 md:pl-64 transition-all duration-300",
        ThemeBackgrounds[DEFAULT_THEME],
      )}
    >
      <Sidebar />

      <main className="px-6 py-8 md:p-12 max-w-7xl mx-auto space-y-8">
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

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Stats & Analysis */}
          <div className="lg:col-span-1 space-y-6">
            {/* Guard Score Card */}
            <Card className="bg-[#040d07] border border-white/5 shadow-2xl rounded-[24px] relative overflow-hidden">
              <div className="absolute top-0 right-0 p-32 bg-emerald-500/5 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2" />
              <CardContent className="p-8 relative">
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-2">
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
                </div>

                <div className="flex items-end gap-3 mb-4">
                  <div className="flex items-baseline">
                    <span className="text-7xl font-black tracking-tighter text-emerald-500 drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                      {data?.guard_score || (isLoading ? "..." : "0")}
                    </span>
                    <span className="text-2xl font-bold text-gray-500 ml-2">
                      / 100
                    </span>
                  </div>
                  <div className="mb-2">
                    <span
                      className={cn(
                        "font-bold text-lg px-2 py-1 rounded-md border",
                        trendAnalysis.avgChange >= 0
                          ? "text-emerald-500 border-emerald-500/20 bg-emerald-500/10"
                          : "text-red-400 border-red-400/20 bg-red-400/5",
                      )}
                    >
                      {trendAnalysis.avgChange > 0 ? "+" : ""}
                      {Math.round(trendAnalysis.avgChange * 10)}%
                    </span>
                  </div>
                </div>
                <p className="text-muted-foreground text-sm font-medium mb-6">
                  {(() => {
                    if (!data) return "Loading financial status...";

                    const overBudgetCount = data.allocation_health.filter(
                      (item) => item.status === "Over Budget",
                    ).length;
                    const nearCapacityCount = data.allocation_health.filter(
                      (item) => item.status === "Near Capacity",
                    ).length;

                    // Critical: Over budget categories exist
                    if (overBudgetCount > 0) {
                      return `Vigilance required • ${overBudgetCount} ${overBudgetCount === 1 ? "category" : "categories"} over budget`;
                    }

                    // Warning: Near capacity
                    if (nearCapacityCount > 0) {
                      return `Attention needed • ${nearCapacityCount} ${nearCapacityCount === 1 ? "category" : "categories"} near capacity`;
                    }

                    // Guard score based messages
                    if (data.guard_score >= 80) {
                      return "Financial health is optimal • Keep it up";
                    } else if (data.guard_score >= 60) {
                      return "Financial health is stable • Stay consistent";
                    } else {
                      return "Vigilance required • Decision quality needs improvement";
                    }
                  })()}
                </p>

                <div className="flex flex-wrap gap-2">
                  <div className="bg-[#020804] border border-white/5 px-3 py-1.5 rounded-lg flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                    <span className="text-[10px] font-bold uppercase text-gray-500">
                      {data?.allocation_health.filter(
                        (i) => i.status === "Over Budget",
                      ).length || 0}{" "}
                      critical budgets over limit
                    </span>
                  </div>
                  <div className="bg-[#020804] border border-white/5 px-3 py-1.5 rounded-lg flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
                    <span className="text-[10px] font-bold uppercase text-gray-500">
                      {data?.allocation_health.filter(
                        (i) => i.status === "Near Capacity",
                      ).length || 0}{" "}
                      near capacity
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Growth Analysis Card */}
            <Card className="bg-[#040d07] border border-white/5 shadow-2xl rounded-[24px] overflow-hidden flex flex-col">
              <CardContent className="p-8 flex-1 flex flex-col">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                        Growth Analysis
                      </p>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <h2 className="text-xl font-bold text-white">
                        Status:{" "}
                        <span
                          className={cn(
                            data?.status === "Thriving"
                              ? "text-emerald-500"
                              : "text-red-400",
                          )}
                        >
                          {data?.status || (isLoading ? "..." : "At Risk")}
                        </span>
                      </h2>
                    </div>
                    <p className="text-emerald-500 text-xs font-medium mt-1 italic opacity-80">
                      {data?.trend.length || 0} checkpoints active •{" "}
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

                <div className="w-full h-[200px] mt-4 relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={sparklineData}
                      margin={{ top: 10, right: 80, left: 10, bottom: 60 }}
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

          {/* Right Column: Allocation Health */}
          <div className="lg:col-span-1">
            <Card className="bg-[#040d07] border border-white/5 shadow-2xl rounded-[24px] h-full">
              <CardContent className="p-8 h-full flex flex-col">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-lg font-bold text-white uppercase tracking-wide">
                    Allocation Health
                  </h3>
                  <button className="text-emerald-500 text-[10px] font-black uppercase tracking-widest hover:text-white transition-colors">
                    Details
                  </button>
                </div>

                <div className="space-y-7 flex-1">
                  {data?.allocation_health.map((item, idx) => {
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
                      <div key={idx} className="space-y-2">
                        <div className="flex justify-between items-center mb-1">
                          <div className="flex items-center gap-3">
                            <div
                              className={cn(
                                "p-1.5 rounded-lg border border-white/5 bg-emerald-500/10",
                                item.status === "Over Budget"
                                  ? "text-red-500"
                                  : "text-emerald-500",
                              )}
                            >
                              {getCategoryIcon(item.label)}
                            </div>
                            <span className="font-bold text-white text-sm">
                              {item.label}
                            </span>
                          </div>
                          <div className="text-sm">
                            <span className="font-bold text-white">
                              ${item.utilized}
                            </span>
                            <span className="text-muted-foreground/40 text-xs font-medium ml-1">
                              utilized
                            </span>
                          </div>
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

                        <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-wider">
                          <span className="text-muted-foreground/30">
                            Budget Limit: ${item.limit}
                          </span>
                          <span className={statusColor}>{statusText}</span>
                        </div>
                      </div>
                    );
                  })}
                  {(!data || data.allocation_health.length === 0) &&
                    !isLoading && (
                      <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50 space-y-2 min-h-50">
                        <Wallet className="w-8 h-8" />
                        <span className="text-xs uppercase tracking-widest">
                          No allocations set
                        </span>
                      </div>
                    )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Bottom Section: Intercepted Decisions */}
        <section className="space-y-6 pt-4">
          <h3 className="text-lg font-bold text-white">
            Intercepted decisions
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {data?.recent_intercepts.map((item) => (
              <div
                key={item.decision_id}
                className="bg-[#040d07] border border-white/5 p-5 rounded-2xl flex items-center gap-5 group hover:border-emerald-500/20 hover:shadow-emerald-900/10 transition-all shadow-lg"
              >
                <div className="w-10 h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-500 border border-white/5">
                  {getCategoryIcon(item.category)}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-white text-sm truncate">
                    {item.item_name}
                  </h4>
                  <p className="text-[10px] text-muted-foreground/60 font-bold uppercase tracking-wider mt-0.5">
                    {new Date(item.created_at).toLocaleDateString()} •{" "}
                    {item.category}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "w-6 h-6 rounded-full flex items-center justify-center",
                      item.score >= 7 ? "bg-emerald-500" : "bg-red-500",
                    )}
                  >
                    <span className="text-[#020403] text-[10px] font-black">
                      {item.score}
                    </span>
                  </div>
                  <p className="font-bold text-white text-base">
                    ${item.amount.toFixed(2)}
                  </p>
                </div>
              </div>
            ))}
            {(!data || data.recent_intercepts.length === 0) && !isLoading && (
              <div className="col-span-full py-12 text-center text-muted-foreground/50 text-sm italic">
                No intercepted decisions recorded yet.
              </div>
            )}
          </div>
        </section>
      </main>

      <div className="md:hidden">
        <Navbar />
      </div>
    </div>
  );
}
