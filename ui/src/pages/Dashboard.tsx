import { useMemo } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
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
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Plus,
  ShieldCheck,
  History,
  Wallet,
  Utensils,
  Film,
  ShoppingBag,
  ShoppingCart,
  CheckCircle2,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
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
      let dateLabel = `Day ${i + 1}`;

      if (typeof it === "object" && it?.date) {
        try {
          const d = new Date(it.date);
          if (!isNaN(d.getTime())) {
            dateLabel = d.toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            });
          }
        } catch {
          // Fallback
        }
      }

      return {
        date: dateLabel,
        score: score,
        item: name,
      };
    });
  }, [data]);

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
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-primary rounded-full border-[3px] border-[#020403] flex items-center justify-center">
                <ShieldCheck className="w-2.5 h-2.5 text-[#020403] fill-current" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white leading-tight">
                {user?.name || "Welcome Back"}
              </h1>
              <div className="flex items-center gap-1.5 mt-0.5">
                <div className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse" />
                <p className="text-[10px] font-bold uppercase tracking-widest text-primary opacity-90">
                  Guard Active
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <p className="hidden md:block text-xs font-medium text-muted-foreground/60">
              Live guard overview • Updated just now
            </p>
            <Button
              onClick={() => navigate("/chat")}
              className="rounded-full bg-primary text-[#020403] hover:bg-primary/90 transition-all gap-2 px-6 py-5 font-black uppercase tracking-wider text-xs shadow-[0_0_20px_rgba(16,185,129,0.3)]"
            >
              <Plus className="w-4 h-4 stroke-[4px]" />
              Analyze
            </Button>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Stats & Analysis */}
          <div className="lg:col-span-1 space-y-6">
            {/* Guard Score Card */}
            <Card className="bg-[#0A1210] border border-white/5 shadow-xl rounded-[24px] relative overflow-hidden">
              <div className="absolute top-0 right-0 p-32 bg-primary/5 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2" />
              <CardContent className="p-8 relative">
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-2">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                      Guard Score
                    </p>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info className="w-3 h-3 text-muted-foreground/40 hover:text-primary transition-colors" />
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

                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-7xl font-black tracking-tighter text-primary drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                    {data?.guard_score || (isLoading ? "..." : "0")}
                  </span>
                  <span className="text-primary/80 font-bold text-2xl tracking-tight">
                    {data && data.trend.length > 1
                      ? ((data.trend[data.trend.length - 1] as any).score ??
                          (data.trend[data.trend.length - 1] as any)) >=
                        ((data.trend[data.trend.length - 2] as any).score ??
                          (data.trend[data.trend.length - 2] as any))
                        ? "+"
                        : ""
                      : "+"}
                    0%
                  </span>
                </div>
                <p className="text-muted-foreground text-sm font-medium mb-6">
                  {data?.status === "Thriving"
                    ? "Financial health is optimal • Keep it up"
                    : "Vigilance required • Multiple categories at risk"}
                </p>

                <div className="flex flex-wrap gap-2">
                  <div className="bg-[#0F1A16] border border-white/5 px-3 py-1.5 rounded-lg flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
                    <span className="text-[10px] font-bold uppercase text-muted-foreground">
                      {data?.allocation_health.filter(
                        (i) => i.status === "Over Budget",
                      ).length || 0}{" "}
                      critical budgets over limit
                    </span>
                  </div>
                  <div className="bg-[#0F1A16] border border-white/5 px-3 py-1.5 rounded-lg flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
                    <span className="text-[10px] font-bold uppercase text-muted-foreground">
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
            <Card className="bg-[#0A1210] border border-white/5 shadow-xl rounded-[24px] overflow-hidden flex flex-col h-70">
              <CardContent className="p-8 flex-1 flex flex-col">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">
                        Growth Analysis
                      </p>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <h2 className="text-xl font-bold text-white">
                        Status:{" "}
                        <span
                          className={cn(
                            data?.status === "Thriving"
                              ? "text-primary"
                              : "text-red-400",
                          )}
                        >
                          {data?.status || (isLoading ? "..." : "At Risk")}
                        </span>
                      </h2>
                    </div>
                    <p className="text-primary text-xs font-medium mt-1 italic opacity-80">
                      {data?.trend.length || 0} checkpoints active • Spending
                      velocity increasing
                    </p>
                  </div>
                  <div className="bg-[#020403] border border-white/5 p-1 rounded-lg flex text-[10px] font-bold">
                    <span className="px-3 py-1.5 bg-[#0F2922] text-primary rounded-md uppercase cursor-pointer">
                      Week
                    </span>
                    <span className="px-3 py-1.5 text-muted-foreground uppercase opacity-50 cursor-pointer hover:text-white transition-colors">
                      Month
                    </span>
                  </div>
                </div>

                <div className="flex-1 w-full h-[240px] mt-4 relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={sparklineData}
                      margin={{ top: 20, right: 10, left: -20, bottom: 0 }}
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
                        dataKey="date"
                        tick={{ fill: "#52525b", fontSize: 10 }}
                        tickLine={false}
                        axisLine={false}
                        interval="preserveStartEnd"
                        padding={{ left: 10, right: 10 }}
                      />
                      <YAxis
                        tick={{ fill: "#52525b", fontSize: 10 }}
                        tickLine={false}
                        axisLine={false}
                        domain={[0, 10]}
                        ticks={[0, 5, 10]}
                      />
                      <ReferenceLine
                        y={7}
                        stroke="#10b981"
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
                                ? "text-primary"
                                : score >= 4
                                  ? "text-yellow-400"
                                  : "text-red-400";
                            return (
                              <div className="bg-[#0A1210]/90 backdrop-blur-md border border-white/10 p-4 rounded-xl shadow-2xl">
                                <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-2 font-bold">
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
                        activeDot={{
                          r: 6,
                          fill: "#0A1210",
                          stroke: "url(#scoreGradient)",
                          strokeWidth: 3,
                        }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Allocation Health */}
          <div className="lg:col-span-1">
            <Card className="bg-[#0A1210] border border-white/5 shadow-xl rounded-[24px] h-full">
              <CardContent className="p-8 h-full flex flex-col">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-lg font-bold text-white uppercase tracking-wide">
                    Allocation Health
                  </h3>
                  <button className="text-primary text-[10px] font-black uppercase tracking-widest hover:text-white transition-colors">
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
                          : "text-muted-foreground";

                    const progressColor =
                      item.status === "Over Budget"
                        ? "bg-red-500"
                        : item.status === "Near Capacity"
                          ? "bg-yellow-400"
                          : "bg-primary";

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
                                "p-1.5 rounded-lg border border-white/5 bg-[#0F1A16]",
                                item.status === "Over Budget"
                                  ? "text-red-500"
                                  : "text-primary",
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
                className="bg-[#0A1210] border border-white/5 p-5 rounded-2xl flex items-center gap-5 group hover:bg-[#0F1A16] transition-colors"
              >
                <div className="w-10 h-10 bg-[#0F2922] rounded-xl flex items-center justify-center text-primary border border-white/5">
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
                      item.score >= 7 ? "bg-primary" : "bg-red-500",
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

        <footer className="pt-12 pb-4 text-center">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/30">
            Powered by Strands & Opik
          </p>
        </footer>
      </main>

      {/* Floating Shield for Mobile/All */}
      <div className="fixed bottom-24 right-6 md:bottom-8 md:right-8 z-40 md:hidden">
        <div className="w-14 h-14 bg-[#0F2922] border border-primary/20 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.2)]">
          <ShieldCheck className="w-6 h-6 text-primary" />
        </div>
      </div>

      <div className="md:hidden">
        <Navbar />
      </div>
    </div>
  );
}
