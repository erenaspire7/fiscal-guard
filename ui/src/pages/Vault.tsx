import { useState, useMemo } from "react";
import { useVaultData } from "@/hooks/useVaultData";
import { useAuth } from "@/contexts/AuthContext";
import AddGoalModal from "@/components/modals/AddGoalModal";
import AddBudgetModal from "@/components/modals/AddBudgetModal";
import DeleteConfirmationModal from "@/components/modals/DeleteConfirmationModal";
import AddProgressModal from "@/components/modals/AddProgressModal";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { Card, CardContent } from "@/components/ui/card";
import { env } from "@/config/env";
import {
  Plus,
  Wallet,
  Target,
  Trash2,
  ShoppingBag,
  Utensils,
  Film,
  Home,
  PieChart,
  Car,
  Plane,
  Heart,
  GraduationCap,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";

export default function Vault() {
  const [activeTab, setActiveTab] = useState<"budgets" | "goals">("budgets");
  const { budgets, goals, isLoading, refresh } = useVaultData();
  const { token } = useAuth();
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<{
    type: "budgets" | "goals" | "category";
    id: string;
    categoryKey?: string;
  } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [progressModalOpen, setProgressModalOpen] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<{
    id: string;
    name: string;
  } | null>(null);

  const totalBudget = useMemo(() => {
    if (budgets.length === 0) return 0;
    return Number(budgets[0].total_monthly);
  }, [budgets]);

  const goalsSaved = useMemo(() => {
    return goals.reduce((acc, goal) => acc + Number(goal.current_amount), 0);
  }, [goals]);

  const handleDelete = (type: "budgets" | "goals", id: string) => {
    setItemToDelete({ type, id });
    setDeleteModalOpen(true);
  };

  const handleDeleteCategory = (categoryKey: string) => {
    if (budgets.length === 0) return;
    setItemToDelete({
      type: "category",
      id: budgets[0].budget_id,
      categoryKey,
    });
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!token || !itemToDelete) return;

    setIsDeleting(true);
    try {
      if (itemToDelete.type === "category" && itemToDelete.categoryKey) {
        // Remove a single category via PUT
        const budget = budgets[0];
        const updatedCategories = { ...budget.categories };
        delete updatedCategories[itemToDelete.categoryKey];

        const newTotal = Object.values(updatedCategories).reduce(
          (sum, cat) => sum + Number(cat.limit),
          0,
        );

        const response = await fetch(
          `${env.apiUrl}/budgets/${itemToDelete.id}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              categories: updatedCategories,
              total_monthly: newTotal,
            }),
          },
        );
        if (response.ok) {
          refresh();
          setDeleteModalOpen(false);
        }
      } else {
        const response = await fetch(
          `${env.apiUrl}/${itemToDelete.type}/${itemToDelete.id}`,
          {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
          },
        );
        if (response.ok) {
          refresh();
          setDeleteModalOpen(false);
        }
      }
    } catch (error) {
      console.error("Delete failed:", error);
    } finally {
      setIsDeleting(false);
      setItemToDelete(null);
    }
  };

  const handleAddProgress = (goalId: string, goalName: string) => {
    setSelectedGoal({ id: goalId, name: goalName });
    setProgressModalOpen(true);
  };

  const handleProgressClose = () => {
    setProgressModalOpen(false);
    setSelectedGoal(null);
  };

  // Helper to get icon based on budget name
  const getBudgetIcon = (name: string) => {
    const lower = name.toLowerCase();
    if (lower.includes("food") || lower.includes("dining"))
      return <Utensils className="w-5 h-5 text-red-400" />;
    if (lower.includes("grocery") || lower.includes("groceries"))
      return <ShoppingBag className="w-5 h-5 text-yellow-400" />;
    if (lower.includes("entertainment") || lower.includes("fun"))
      return <Film className="w-5 h-5 text-emerald-500" />;
    if (lower.includes("shopping"))
      return <ShoppingBag className="w-5 h-5 text-orange-400" />;
    if (
      lower.includes("transport") ||
      lower.includes("car") ||
      lower.includes("gas")
    )
      return <Car className="w-5 h-5 text-blue-400" />;
    return <PieChart className="w-5 h-5 text-emerald-500" />;
  };

  // Helper to get icon based on goal name
  const getGoalIcon = (name: string) => {
    const lower = name.toLowerCase();
    if (
      lower.includes("house") ||
      lower.includes("home") ||
      lower.includes("down payment")
    )
      return <Home className="w-6 h-6 text-emerald-500" />;
    if (lower.includes("emergency") || lower.includes("safety"))
      return <Heart className="w-6 h-6 text-emerald-500" />;
    if (
      lower.includes("vacation") ||
      lower.includes("travel") ||
      lower.includes("trip")
    )
      return <Plane className="w-6 h-6 text-emerald-500" />;
    if (lower.includes("car") || lower.includes("vehicle"))
      return <Car className="w-6 h-6 text-emerald-500" />;
    if (
      lower.includes("education") ||
      lower.includes("school") ||
      lower.includes("college")
    )
      return <GraduationCap className="w-6 h-6 text-emerald-500" />;
    return <Target className="w-6 h-6 text-emerald-500" />;
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
        <header>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-500 opacity-80">
                Financial Assets
              </p>
              <h1 className="text-3xl font-bold tracking-tight text-white">
                Vault
              </h1>
            </div>
            {/* Mobile FAB */}
            <Button
              size="icon"
              onClick={() => {
                if (activeTab === "budgets") setIsBudgetModalOpen(true);
                else setIsGoalModalOpen(true);
              }}
              className="md:hidden rounded-full bg-emerald-600 text-white hover:bg-emerald-500 w-12 h-12 shadow-lg shadow-emerald-900/20"
            >
              <Plus className="w-6 h-6 stroke-[3px]" />
            </Button>
          </div>
        </header>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-[#040d07] border border-white/5 rounded-[24px] p-6 shadow-xl">
            <CardContent className="p-0 flex flex-col gap-3">
              <div className="flex items-center gap-2 text-gray-500">
                <div className="w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center">
                  <Wallet className="w-4 h-4" />
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider">
                  Total Budget
                </span>
              </div>
              <p className="text-4xl font-black text-white tracking-tight">
                $
                {totalBudget.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
              <p className="text-[10px] text-gray-500 font-medium">
                Monthly allocation across{" "}
                {budgets.length > 0
                  ? Object.keys(budgets[0].categories).length
                  : 0}{" "}
                categories
              </p>
            </CardContent>
          </Card>
          <Card className="bg-[#040d07] border border-emerald-500/10 rounded-[24px] p-6 shadow-xl">
            <CardContent className="p-0 flex flex-col gap-3">
              <div className="flex items-center gap-2 text-emerald-500/80">
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                  <Target className="w-4 h-4 text-emerald-500" />
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider">
                  Goals Saved
                </span>
              </div>
              <p className="text-4xl font-black text-emerald-500 tracking-tight">
                $
                {goalsSaved.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
              <div className="flex items-center gap-1.5 text-[10px] text-emerald-500/60 font-medium">
                <TrendingUp className="w-3 h-3" />
                <span>
                  {goals.length} active {goals.length === 1 ? "goal" : "goals"}{" "}
                  in progress
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Mobile Tab Toggle */}
        <div className="md:hidden bg-white/5 p-1 rounded-2xl flex">
          <button
            onClick={() => setActiveTab("budgets")}
            className={cn(
              "flex-1 py-3 text-xs font-bold uppercase tracking-widest rounded-xl transition-all",
              activeTab === "budgets"
                ? "bg-emerald-600 text-white"
                : "text-gray-500 opacity-50",
            )}
          >
            Budgets
          </button>
          <button
            onClick={() => setActiveTab("goals")}
            className={cn(
              "flex-1 py-3 text-xs font-bold uppercase tracking-widest rounded-xl transition-all",
              activeTab === "goals"
                ? "bg-emerald-600 text-white"
                : "text-gray-500 opacity-50",
            )}
          >
            Goals
          </button>
        </div>

        {/* Active Budgets Section - Full Width on Desktop */}
        <section
          className={cn(
            "space-y-5",
            activeTab === "goals" && "hidden md:block",
          )}
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2 text-white">
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                  <PieChart className="w-4 h-4 text-emerald-500" />
                </div>
                Active Budgets
              </h3>
              <p className="text-[10px] font-bold text-muted-foreground/40 uppercase tracking-wider ml-10 mt-1">
                {budgets.length > 0
                  ? Object.keys(budgets[0].categories).length
                  : 0}{" "}
                categories
              </p>
            </div>
            {/* Create Budget / Add Category Button Group */}
            <ButtonGroup className="hidden md:flex">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsBudgetModalOpen(true)}
                className="border-white/10 hover:bg-white/10 hover:text-white text-xs font-bold gap-2"
              >
                <Plus className="w-4 h-4" />
                {budgets.length > 0 ? "Add Category" : "Create Budget"}
              </Button>
            </ButtonGroup>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="bg-[#040d07] border border-white/5 rounded-[20px] p-5 animate-pulse"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-white/10" />
                    <div className="h-4 w-24 bg-white/10 rounded" />
                  </div>
                  <div className="space-y-3">
                    <div className="h-6 w-32 bg-white/10 rounded" />
                    <div className="h-2 w-full bg-white/5 rounded-full" />
                  </div>
                </div>
              ))}
            </div>
          ) : budgets.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(budgets[0].categories).map(([name, data]) => {
                const spent = Number(data.spent);
                const limit = Number(data.limit);
                const title = name
                  .replace("_", " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase());
                const percent = Math.min((spent / limit) * 100, 100);
                const actualPercent = (spent / limit) * 100;
                let colorClass = "bg-emerald-500";
                let textClass = "text-emerald-500";
                let statusText = `${Math.round(percent)}% USED`;
                let borderClass = "border-white/5 hover:border-white/10";

                if (actualPercent >= 100) {
                  colorClass = "bg-red-500";
                  textClass = "text-red-500";
                  statusText = "OVER LIMIT";
                  borderClass = "border-red-500/20 hover:border-red-500/30";
                } else if (percent > 85) {
                  colorClass = "bg-yellow-400";
                  textClass = "text-yellow-400";
                  borderClass =
                    "border-yellow-400/20 hover:border-yellow-400/30";
                }

                return (
                  <div
                    key={name}
                    className={cn(
                      "bg-[#040d07] border rounded-[20px] p-5 relative group hover:border-emerald-500/20 hover:shadow-emerald-900/10 transition-all duration-300 shadow-lg",
                      borderClass,
                    )}
                  >
                    <button
                      onClick={() => handleDeleteCategory(name)}
                      className="absolute top-4 right-4 text-muted-foreground/20 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <div className="flex items-center gap-3 mb-4">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-xl flex items-center justify-center transition-colors",
                          actualPercent >= 100
                            ? "bg-red-500/10"
                            : actualPercent > 85
                              ? "bg-yellow-400/10"
                              : "bg-white/5 group-hover:bg-emerald-500/10",
                        )}
                      >
                        {getBudgetIcon(name)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-bold text-white truncate">
                          {title}
                        </h4>
                        <p className="text-[10px] text-muted-foreground/50 font-medium">
                          $
                          {(limit - spent > 0
                            ? limit - spent
                            : 0
                          ).toLocaleString()}{" "}
                          remaining
                        </p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between items-end">
                        <p className="text-xl font-bold text-white">
                          ${spent.toLocaleString()}{" "}
                          <span className="text-xs text-muted-foreground/50 font-medium">
                            / ${limit.toLocaleString()}
                          </span>
                        </p>
                      </div>
                      <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all duration-1000 ease-out",
                            colorClass,
                          )}
                          style={{ width: `${Math.min(percent, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-end">
                        <span
                          className={cn(
                            "text-[9px] font-black uppercase tracking-widest",
                            textClass,
                          )}
                        >
                          {statusText}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-[#040d07] border border-white/5 rounded-[24px] p-10 text-center shadow-xl">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-white/5 flex items-center justify-center">
                <Wallet className="w-8 h-8 text-gray-500/30" />
              </div>
              <p className="text-gray-500 font-medium mb-1">
                No budgets active
              </p>
              <p className="text-[10px] text-gray-500/50">
                Create your first budget to start tracking
              </p>
            </div>
          )}
        </section>

        {/* Active Goals Section - Full Width on Desktop */}
        <section
          className={cn(
            "space-y-5",
            activeTab === "budgets" && "hidden md:block",
          )}
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2 text-white">
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                  <Target className="w-4 h-4 text-emerald-500" />
                </div>
                Active Goals
              </h3>
              <p className="text-[10px] font-bold text-gray-500/40 uppercase tracking-wider ml-10 mt-1">
                {goals.length} {goals.length === 1 ? "goal" : "goals"}
              </p>
            </div>
            {/* Add New Goal Button Group */}
            <ButtonGroup className="hidden md:flex">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsGoalModalOpen(true)}
                className="border-emerald-500/20 hover:bg-emerald-500/20 text-emerald-500 hover:text-emerald-400 text-xs font-bold gap-2"
              >
                <Plus className="w-4 h-4" />
                Add New Goal
              </Button>
            </ButtonGroup>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2].map((i) => (
                <div
                  key={i}
                  className="bg-[#040d07] border border-white/5 rounded-[20px] p-5 flex gap-5 animate-pulse"
                >
                  <div className="w-16 h-16 rounded-full bg-white/10 shrink-0" />
                  <div className="flex-1 space-y-3">
                    <div className="h-5 w-32 bg-white/10 rounded" />
                    <div className="h-3 w-20 bg-white/5 rounded" />
                    <div className="h-6 w-24 bg-white/10 rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : goals.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {goals.map((goal) => {
                const current = Number(goal.current_amount);
                const target = Number(goal.target_amount);
                const percent = Math.min((current / target) * 100, 100);
                const isComplete = percent >= 100;

                return (
                  <div
                    key={goal.goal_id}
                    className={cn(
                      "bg-[#040d07] border rounded-[20px] p-5 flex gap-5 relative group hover:border-emerald-500/20 hover:shadow-emerald-900/10 transition-all duration-300 shadow-lg",
                      isComplete
                        ? "border-emerald-500/20"
                        : "border-white/5 hover:border-white/10",
                    )}
                  >
                    <button
                      onClick={() => handleDelete("goals", goal.goal_id)}
                      className="absolute top-4 right-4 text-muted-foreground/20 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>{" "}
                    {/* Circular Progress */}
                    <div className="relative w-16 h-16 shrink-0">
                      <svg
                        className="w-full h-full -rotate-90"
                        viewBox="0 0 64 64"
                      >
                        <circle
                          cx="32"
                          cy="32"
                          r="28"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="5"
                          className="text-white/5"
                        />
                        <circle
                          cx="32"
                          cy="32"
                          r="28"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="5"
                          strokeDasharray={175.9}
                          strokeDashoffset={175.9 - (175.9 * percent) / 100}
                          strokeLinecap="round"
                          className="text-emerald-500 transition-all duration-1000"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        {isComplete ? (
                          <Sparkles className="w-5 h-5 text-emerald-500" />
                        ) : (
                          getGoalIcon(goal.goal_name)
                        )}
                      </div>
                    </div>
                    <div className="flex-1 flex flex-col justify-center min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h4 className="font-bold text-white truncate">
                          {goal.goal_name}
                        </h4>
                        {isComplete && (
                          <span className="shrink-0 text-[9px] font-black uppercase tracking-wider text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded-md">
                            Complete!
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-gray-500/60 font-medium mb-2">
                        Target:{" "}
                        {goal.deadline
                          ? new Date(goal.deadline).toLocaleDateString(
                              undefined,
                              {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                              },
                            )
                          : "Ongoing"}
                      </p>
                      <div className="flex items-end justify-between gap-3">
                        <div>
                          <p className="text-lg font-bold text-white">
                            ${current.toLocaleString()}
                            <span className="text-xs text-muted-foreground/50 font-medium ml-1">
                              / ${target.toLocaleString()}
                            </span>
                          </p>
                        </div>
                        {!isComplete && (
                          <ButtonGroup>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                handleAddProgress(goal.goal_id, goal.goal_name)
                              }
                              className="border-emerald-500/20 hover:bg-emerald-500/20 text-emerald-500 hover:text-emerald-400 text-xs font-bold gap-2"
                            >
                              <Plus className="w-3 h-3" />
                              Add Progress
                            </Button>
                          </ButtonGroup>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-[#040d07] border border-white/5 rounded-[24px] p-10 text-center shadow-xl">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-emerald-500/5 flex items-center justify-center">
                <Target className="w-8 h-8 text-emerald-500/30" />
              </div>
              <p className="text-gray-500 font-medium mb-1">No active goals</p>
              <p className="text-[10px] text-gray-500/50">
                Set your first goal to start saving
              </p>
            </div>
          )}
        </section>
      </main>

      <div className="md:hidden">
        <Navbar />
      </div>

      <AddBudgetModal
        isOpen={isBudgetModalOpen}
        onClose={() => setIsBudgetModalOpen(false)}
        onSuccess={refresh}
        token={token}
        existingBudget={budgets.length > 0 ? budgets[0] : null}
      />

      <AddGoalModal
        isOpen={isGoalModalOpen}
        onClose={() => setIsGoalModalOpen(false)}
        onSuccess={refresh}
        token={token}
      />

      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        isDeleting={isDeleting}
        title={`Delete ${itemToDelete?.type === "category" ? "Category" : itemToDelete?.type === "budgets" ? "Budget" : "Goal"}`}
        description={`Are you sure you want to remove this ${
          itemToDelete?.type === "category"
            ? "budget category"
            : itemToDelete?.type === "budgets"
              ? "budget plan"
              : "financial goal"
        }? This action cannot be undone.`}
      />

      <AddProgressModal
        isOpen={progressModalOpen && selectedGoal !== null}
        onClose={handleProgressClose}
        onSuccess={refresh}
        token={token}
        goalId={selectedGoal?.id || ""}
        goalName={selectedGoal?.name || ""}
      />
    </div>
  );
}
