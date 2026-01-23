import { useMemo } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { useDashboardData } from "@/hooks/useDashboardData";
import { AreaChart, Area, ResponsiveContainer } from "recharts";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Plus,
  ShieldCheck,
  History,
  Wallet,
  Utensils,
  Film,
  Bus,
  ShoppingBag,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data, isLoading } = useDashboardData();

  const sparklineData = useMemo(() => {
    return (data?.trend || [4, 7, 5, 8, 6, 9, 7, 8]).map((val, i) => ({
      name: i,
      score: val,
    }));
  }, [data]);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans pb-32">
      {/* Header */}
      <header className="px-6 py-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <img
              src={
                user?.picture ||
                `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || user?.email?.split("@")[0] || "user"}`
              }
              alt="Profile"
              className="w-12 h-12 rounded-full border-2 border-primary/20"
            />
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-primary rounded-full border-2 border-background flex items-center justify-center">
              <ShieldCheck className="w-2.5 h-2.5 text-background" />
            </div>
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-primary opacity-80">
              Guard Active
            </p>
            <h1 className="text-xl font-bold leading-tight">
              {user?.name || user?.email?.split("@")[0] || "User"}
            </h1>
          </div>
        </div>
        <Button
          size="sm"
          onClick={() => navigate("/chat")}
          className="rounded-full bg-primary text-background hover:bg-primary/90 transition-all gap-1.5 px-5 py-5 shadow-primary-glow"
        >
          <Plus className="w-5 h-5 stroke-[3px]" />
          <span className="font-bold text-base">Analyze</span>
        </Button>
      </header>

      <main className="px-6 space-y-10">
        {/* Guard Score Card */}
        <Card className="bg-card/50 border-none shadow-xl overflow-hidden relative rounded-[32px]">
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-muted-foreground text-sm font-medium">
                  Guard Score
                </p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-5xl font-bold tracking-tight text-primary text-glow">
                    {data?.guard_score || (isLoading ? "..." : "0")}
                  </span>
                  <span className="text-primary font-bold text-lg text-glow">
                    {data && data.trend.length > 1
                      ? data.trend[data.trend.length - 1] >=
                        data.trend[data.trend.length - 2]
                        ? "+"
                        : ""
                      : ""}
                    {data && data.trend.length > 1
                      ? Math.round(
                          ((data.trend[data.trend.length - 1] -
                            data.trend[data.trend.length - 2]) /
                            data.trend[data.trend.length - 2]) *
                            100,
                        )
                      : "0"}
                    %
                  </span>
                </div>
                <p className="text-muted-foreground text-sm mt-2 font-medium">
                  {data?.status === "Thriving"
                    ? "Prosperous discipline this week"
                    : data?.status === "Stable"
                      ? "Steady financial guard"
                      : "Vigilance required"}
                </p>
              </div>
              <ShieldCheck className="w-6 h-6 text-primary" />
            </div>
          </CardContent>
        </Card>

        {/* Growth Analysis Card */}
        <Card className="bg-card/50 border-none shadow-xl overflow-hidden rounded-[32px]">
          <CardContent className="p-6">
            <div className="flex justify-between items-center mb-1">
              <p className="text-muted-foreground text-sm font-medium">
                Growth Analysis
              </p>
              <div className="bg-background/40 p-0.5 rounded-lg flex">
                <button className="px-3 py-1 text-[10px] font-bold rounded-md bg-primary/20 text-primary uppercase">
                  Week
                </button>
                <button className="px-3 py-1 text-[10px] font-bold rounded-md text-muted-foreground uppercase opacity-40">
                  Month
                </button>
              </div>
            </div>

            <h2 className="text-2xl font-bold">
              Status:{" "}
              {data?.status || (isLoading ? "Analyzing..." : "Awaiting Data")}
            </h2>
            <p className="text-primary text-xs font-medium mt-1 text-glow">
              Intelligence Trend{" "}
              <span className="font-bold">
                {data?.trend.length || 0} checkpoints active
              </span>
            </p>

            {/* Sparkline Visual - High Fidelity with Recharts */}
            <div className="h-32 mt-6 relative w-full overflow-hidden">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sparklineData}>
                  <defs>
                    <linearGradient
                      id="dashGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#10b981"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#dashGradient)"
                    animationDuration={1500}
                    isAnimationActive={true}
                  />
                </AreaChart>
              </ResponsiveContainer>
              <div className="flex justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-2 opacity-50">
                <span>Mon</span>
                <span>Wed</span>
                <span>Fri</span>
                <span>Sun</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Allocation Health Section */}
        <section className="space-y-5">
          <div className="flex justify-between items-end px-1">
            <h3 className="text-xl font-bold tracking-tight">
              Allocation Health
            </h3>
            <button className="text-primary text-sm font-bold opacity-80">
              Details
            </button>
          </div>

          <div className="space-y-3">
            {data?.allocation_health.map((item, idx) => (
              <div
                key={idx}
                className="bg-card/50 p-5 rounded-[24px] space-y-3"
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Wallet className="w-4 h-4 text-primary" />
                    </div>
                    <span className="font-bold text-sm">{item.label}</span>
                  </div>
                  <div className="text-sm">
                    <span className="font-bold">
                      ${item.utilized.toLocaleString()}
                    </span>
                    <span className="text-muted-foreground ml-1">utilized</span>
                  </div>
                </div>
                <div className="h-1.5 w-full bg-background rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full shadow-primary-glow transition-all duration-500"
                    style={{ width: `${Math.min(100, item.percentage)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider">
                  <span className="text-muted-foreground opacity-60">
                    Budget Limit: ${item.limit.toLocaleString()}
                  </span>
                  <span
                    className={cn(
                      "text-glow",
                      item.status === "Healthy"
                        ? "text-primary"
                        : item.status === "Near Capacity"
                          ? "text-[#a4f4e0]"
                          : "text-destructive",
                    )}
                  >
                    {item.status}
                  </span>
                </div>
              </div>
            ))}
            {(!data || data.allocation_health.length === 0) && !isLoading && (
              <p className="text-center text-muted-foreground text-sm py-4">
                No active budgets found.
              </p>
            )}
          </div>
        </section>

        {/* Intercepted Decisions Section */}
        <section className="space-y-5">
          <div className="flex justify-between items-end px-1">
            <h3 className="text-xl font-bold tracking-tight">
              Intercepted Decisions
            </h3>
            <History className="w-5 h-5 text-primary opacity-80" />
          </div>

          <div className="space-y-3">
            {data?.recent_intercepts.map((item, i) => (
              <div
                key={item.decision_id}
                className="bg-card/50 p-4 rounded-[24px] flex items-center gap-4"
              >
                <div className="w-12 h-12 bg-background/40 rounded-2xl flex items-center justify-center">
                  <ShoppingBag className="w-6 h-6 text-primary/70" />
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-sm">{item.item_name}</h4>
                  <p className="text-[11px] text-muted-foreground font-medium">
                    {new Date(item.created_at).toLocaleDateString()} •{" "}
                    {item.category}
                  </p>
                </div>
                <div className="text-right">
                  <div className="inline-flex items-center justify-center bg-primary text-background text-[10px] font-bold w-6 h-6 rounded-full mb-1 shadow-primary-glow">
                    {item.score}
                  </div>
                  <p className="font-bold text-sm leading-none">
                    ${item.amount.toFixed(2)}
                  </p>
                </div>
              </div>
            ))}
            {(!data || data.recent_intercepts.length === 0) && !isLoading && (
              <p className="text-center text-muted-foreground text-sm py-4">
                No recent decisions intercepted.
              </p>
            )}
          </div>
        </section>
      </main>

      {/* Bottom Navigation */}
      <Navbar />
    </div>
  );
}
