import { useState, useMemo } from "react";
import { useVaultData } from "@/hooks/useVaultData";
import { useAuth } from "@/contexts/AuthContext";
import AddGoalModal from "@/components/modals/AddGoalModal";
import AddBudgetModal from "@/components/modals/AddBudgetModal";
import DeleteConfirmationModal from "@/components/modals/DeleteConfirmationModal";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Plus,
  Wallet,
  Target,
  TrendingUp,
  ChevronRight,
  PieChart,
  ArrowUpRight,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function Vault() {
  const [activeTab, setActiveTab] = useState<"budgets" | "goals">("budgets");
  const { budgets, goals, isLoading, refresh } = useVaultData();
  const { token } = useAuth();
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<{
    type: "budgets" | "goals";
    id: string;
  } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [progressModalOpen, setProgressModalOpen] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [progressAmount, setProgressAmount] = useState("");
  const [isSubmittingProgress, setIsSubmittingProgress] = useState(false);

  const totalBudget = useMemo(() => {
    if (budgets.length === 0) return 0;
    // Summing total_monthly from the first (active) budget for simplicity
    return budgets[0].total_monthly;
  }, [budgets]);

  const goalsSaved = useMemo(() => {
    return goals.reduce((acc, goal) => acc + goal.current_amount, 0);
  }, [goals]);

  const handleDelete = (type: "budgets" | "goals", id: string) => {
    setItemToDelete({ type, id });
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!token || !itemToDelete) return;

    setIsDeleting(true);
    try {
      const response = await fetch(
        `${
          import.meta.env.VITE_API_URL || "http://localhost:8000"
        }/${itemToDelete.type}/${itemToDelete.id}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (response.ok) {
        refresh();
        setDeleteModalOpen(false);
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
    setProgressAmount("");
    setProgressModalOpen(true);
  };

  const submitProgress = async () => {
    if (!token || !selectedGoal || !progressAmount) return;

    const amount = parseFloat(progressAmount);
    if (isNaN(amount) || amount <= 0) return;

    setIsSubmittingProgress(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/goals/${selectedGoal.id}/progress`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ amount }),
        },
      );

      if (response.ok) {
        refresh();
        setProgressModalOpen(false);
        setSelectedGoal(null);
        setProgressAmount("");
      }
    } catch (error) {
      console.error("Failed to add progress:", error);
    } finally {
      setIsSubmittingProgress(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans pb-32">
      {/* Header */}
      <header className="px-6 py-8 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-primary opacity-80">
            Financial Assets
          </p>
          <h1 className="text-3xl font-bold tracking-tight">Vault</h1>
        </div>
        <Button
          size="icon"
          onClick={() => {
            if (activeTab === "budgets") setIsBudgetModalOpen(true);
            else setIsGoalModalOpen(true);
          }}
          className="rounded-full bg-primary text-background hover:bg-primary/90 shadow-primary-glow w-12 h-12"
        >
          <Plus className="w-6 h-6 stroke-[3px]" />
        </Button>
      </header>

      {/* Summary Cards */}
      <div className="px-6 grid grid-cols-2 gap-4 mb-8">
        <Card className="bg-card/40 border-none rounded-[24px]">
          <CardContent className="p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Wallet className="w-3 h-3" />
              <span className="text-[10px] font-bold uppercase tracking-wider">
                Total Budget
              </span>
            </div>
            <p className="text-xl font-bold">${totalBudget.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className="bg-card/40 border-none rounded-[24px]">
          <CardContent className="p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Target className="w-3 h-3" />
              <span className="text-[10px] font-bold uppercase tracking-wider">
                Goals Saved
              </span>
            </div>
            <p className="text-xl font-bold text-primary text-glow">
              ${goalsSaved.toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="px-6 mb-6">
        <div className="bg-card/30 p-1 rounded-2xl flex">
          <button
            onClick={() => setActiveTab("budgets")}
            className={cn(
              "flex-1 py-3 text-xs font-bold uppercase tracking-widest rounded-xl transition-all",
              activeTab === "budgets"
                ? "bg-primary text-background shadow-primary-glow"
                : "text-muted-foreground opacity-50",
            )}
          >
            Budgets
          </button>
          <button
            onClick={() => setActiveTab("goals")}
            className={cn(
              "flex-1 py-3 text-xs font-bold uppercase tracking-widest rounded-xl transition-all",
              activeTab === "goals"
                ? "bg-primary text-background shadow-primary-glow"
                : "text-muted-foreground opacity-50",
            )}
          >
            Goals
          </button>
        </div>
      </div>

      <main className="px-6 space-y-4">
        {isLoading ? (
          <div className="text-center py-20 text-muted-foreground animate-pulse font-bold tracking-widest uppercase text-xs">
            Unlocking Vault...
          </div>
        ) : activeTab === "budgets" ? (
          <>
            {budgets.length > 0 ? (
              Object.entries(budgets[0].categories).map(([name, data]) => {
                const percent = (data.spent / data.limit) * 100;
                let color: "primary" | "warning" | "danger" = "primary";
                if (percent >= 100) color = "danger";
                else if (percent >= 80) color = "warning";

                return (
                  <BudgetCard
                    key={name}
                    title={name
                      .replace("_", " ")
                      .replace(/\b\w/g, (l) => l.toUpperCase())}
                    spent={data.spent}
                    limit={data.limit}
                    color={color}
                    onDelete={() =>
                      handleDelete("budgets", budgets[0].budget_id)
                    }
                  />
                );
              })
            ) : (
              <p className="text-center text-muted-foreground text-sm py-10">
                No budgets defined in the vault.
              </p>
            )}
          </>
        ) : (
          <>
            {goals.length > 0 ? (
              goals.map((goal) => (
                <GoalCard
                  key={goal.goal_id}
                  title={goal.goal_name}
                  current={goal.current_amount}
                  target={goal.target_amount}
                  date={
                    goal.deadline
                      ? new Date(goal.deadline).toLocaleDateString()
                      : "Ongoing"
                  }
                  onDelete={() => handleDelete("goals", goal.goal_id)}
                  onAddProgress={() =>
                    handleAddProgress(goal.goal_id, goal.goal_name)
                  }
                />
              ))
            ) : (
              <p className="text-center text-muted-foreground text-sm py-10">
                No financial goals established.
              </p>
            )}
          </>
        )}
      </main>

      <Navbar />

      <AddBudgetModal
        isOpen={isBudgetModalOpen}
        onClose={() => setIsBudgetModalOpen(false)}
        onSuccess={refresh}
        token={token}
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
        title={`Delete ${itemToDelete?.type === "budgets" ? "Budget" : "Goal"}`}
        description={`Are you sure you want to remove this ${
          itemToDelete?.type === "budgets" ? "budget plan" : "financial goal"
        }? This action cannot be undone.`}
      />

      {/* Add Progress Modal */}
      {progressModalOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-end justify-center z-50 backdrop-blur-sm">
          <div className="bg-card w-full max-w-md rounded-t-[32px] p-6 space-y-6 animate-slide-up">
            <div className="space-y-2">
              <h3 className="text-xl font-bold">Add Progress</h3>
              <p className="text-sm text-muted-foreground">
                Contribute to:{" "}
                <span className="text-primary font-bold">
                  {selectedGoal?.name}
                </span>
              </p>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Amount ($)
              </label>
              <input
                type="number"
                value={progressAmount}
                onChange={(e) => setProgressAmount(e.target.value)}
                placeholder="0.00"
                step="0.01"
                min="0"
                className="w-full bg-background border border-white/5 rounded-2xl py-4 px-5 text-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => {
                  setProgressModalOpen(false);
                  setSelectedGoal(null);
                  setProgressAmount("");
                }}
                variant="outline"
                className="flex-1 h-12 rounded-xl"
                disabled={isSubmittingProgress}
              >
                Cancel
              </Button>
              <Button
                onClick={submitProgress}
                disabled={
                  !progressAmount ||
                  isSubmittingProgress ||
                  parseFloat(progressAmount) <= 0
                }
                className="flex-1 h-12 rounded-xl bg-primary text-background hover:bg-primary/90 shadow-primary-glow"
              >
                {isSubmittingProgress ? "Adding..." : "Add Progress"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function BudgetCard({
  title,
  spent,
  limit,
  onDelete,
  color = "primary",
}: {
  title: string;
  spent: number;
  limit: number;
  onDelete?: () => void;
  color?: "primary" | "warning" | "danger";
}) {
  const percentage = Math.min((spent / limit) * 100, 100);
  const colorClass =
    color === "danger"
      ? "bg-red-500"
      : color === "warning"
        ? "bg-yellow-400"
        : "bg-primary";

  return (
    <Card className="bg-card/50 border-none shadow-lg rounded-[28px] overflow-hidden group active:scale-[0.98] transition-transform">
      <CardContent className="p-5 space-y-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-background/40 rounded-xl flex items-center justify-center">
              <PieChart className="w-5 h-5 text-primary/70" />
            </div>
            <h4 className="font-bold text-sm">{title}</h4>
          </div>
          <div className="flex items-center gap-2">
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="p-2 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <ArrowUpRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-end">
            <p className="text-xl font-bold">
              ${spent}{" "}
              <span className="text-xs text-muted-foreground font-medium">
                / ${limit}
              </span>
            </p>
            <span
              className={cn(
                "text-[10px] font-bold uppercase tracking-wider",
                percentage > 90 ? "text-red-400" : "text-primary opacity-80",
              )}
            >
              {Math.round(percentage)}% used
            </span>
          </div>
          <div className="h-2 w-full bg-background rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-1000 shadow-primary-glow",
                colorClass,
              )}
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function GoalCard({
  title,
  current,
  target,
  date,
  onDelete,
  onAddProgress,
}: {
  title: string;
  current: number;
  target: number;
  date: string;
  onDelete: () => void;
  onAddProgress: () => void;
}) {
  const percentage = Math.min((current / target) * 100, 100);

  return (
    <Card className="bg-card/50 border-none shadow-lg rounded-[28px] overflow-hidden">
      <CardContent className="p-5 flex items-center gap-4">
        <div className="relative w-16 h-16 shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 64 64">
            <circle
              cx="32"
              cy="32"
              r="28"
              fill="none"
              stroke="currentColor"
              strokeWidth="5"
              className="text-background"
            />
            <circle
              cx="32"
              cy="32"
              r="28"
              fill="none"
              stroke="currentColor"
              strokeWidth="5"
              strokeDasharray={175.9}
              strokeDashoffset={175.9 - (175.9 * percentage) / 100}
              strokeLinecap="round"
              className="text-primary transition-all duration-1000"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-primary" />
          </div>
        </div>

        <div className="flex-1">
          <div className="flex justify-between items-start">
            <h4 className="font-bold text-sm leading-tight">{title}</h4>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="p-1 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded-lg transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
          <p className="text-[10px] text-muted-foreground font-medium mt-0.5">
            Target: {date}
          </p>
          <div className="flex items-center justify-between gap-2 mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-bold">
                ${current.toLocaleString()}
              </span>
              <span className="text-[10px] text-muted-foreground font-bold uppercase opacity-60">
                of ${target.toLocaleString()}
              </span>
            </div>
            <Button
              onClick={(e) => {
                e.stopPropagation();
                onAddProgress();
              }}
              size="sm"
              className="h-7 px-3 rounded-lg bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 text-xs font-bold"
            >
              <Plus className="w-3 h-3 mr-1" />
              Add $
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
