import React, { useState } from "react";
import { X, Wallet, Plus, Trash2, Calendar, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { env } from "@/config/env";

interface CategoryEntry {
  id: string;
  name: string;
  limit: string;
}

interface AddBudgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  token: string | null;
}

export default function AddBudgetModal({
  isOpen,
  onClose,
  onSuccess,
  token,
}: AddBudgetModalProps) {
  const [name, setName] = useState("");
  const [totalMonthly, setTotalMonthly] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [categories, setCategories] = useState<CategoryEntry[]>([
    {
      id: Math.random().toString(36).substr(2, 9),
      name: "Groceries",
      limit: "",
    },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const addCategory = () => {
    setCategories([
      ...categories,
      { id: Math.random().toString(36).substr(2, 9), name: "", limit: "" },
    ]);
  };

  const removeCategory = (id: string) => {
    if (categories.length > 1) {
      setCategories(categories.filter((cat) => cat.id !== id));
    }
  };

  const updateCategory = (
    id: string,
    field: keyof CategoryEntry,
    value: string,
  ) => {
    setCategories(
      categories.map((cat) =>
        cat.id === id ? { ...cat, [field]: value } : cat,
      ),
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsSubmitting(true);
    try {
      // Format categories into the expected Record<string, CategoryBudget>
      const categoriesMap: Record<string, { limit: number; spent: number }> =
        {};
      categories.forEach((cat) => {
        if (cat.name) {
          categoriesMap[cat.name.toLowerCase().replace(/\s+/g, "_")] = {
            limit: parseFloat(cat.limit) || 0,
            spent: 0,
          };
        }
      });

      const response = await fetch(`${env.apiUrl}/budgets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          total_monthly: parseFloat(totalMonthly),
          period_start: periodStart,
          period_end: periodEnd,
          categories: categoriesMap,
        }),
      });

      if (response.ok) {
        onSuccess();
        onClose();
      }
    } catch (error) {
      console.error("Failed to create budget:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
      <Card className="w-full max-w-xl bg-[#0A1210] border-white/5 shadow-2xl rounded-[32px] overflow-hidden max-h-[90vh] flex flex-col animate-in slide-in-from-bottom-8 duration-500 text-foreground">
        <div className="absolute top-6 right-6 z-10">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="rounded-full hover:bg-white/5 text-muted-foreground hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        <CardContent className="p-8 space-y-8 overflow-y-auto custom-scrollbar">
          <div className="space-y-2">
            <div className="w-12 h-12 bg-[#0F2922] rounded-2xl flex items-center justify-center mb-4 border border-primary/20">
              <Wallet className="w-6 h-6 text-primary shadow-[0_0_10px_rgba(16,185,129,0.4)]" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">
              Establish Budget
            </h2>
            <p className="text-sm text-muted-foreground">
              Define the boundaries of your financial guard for this period.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Budget Name */}
              <div className="space-y-2 sm:col-span-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60 ml-1">
                  Budget Reference Name
                </label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Q1 2026 Strategic Plan"
                  className="w-full bg-[#020403] border border-white/10 rounded-2xl px-4 py-4 focus:outline-none focus:border-primary/50 transition-all font-medium text-white placeholder:text-muted-foreground/50"
                />
              </div>

              {/* Total Limit */}
              <div className="space-y-2 sm:col-span-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60 ml-1">
                  Total Monthly Limit ($)
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-primary opacity-60">
                    $
                  </span>
                  <input
                    required
                    type="number"
                    value={totalMonthly}
                    onChange={(e) => setTotalMonthly(e.target.value)}
                    placeholder="4000"
                    className="w-full bg-[#020403] border border-white/10 rounded-2xl pl-8 pr-4 py-4 focus:outline-none focus:border-primary/50 transition-all font-bold text-xl text-white placeholder:text-muted-foreground/50"
                  />
                </div>
              </div>

              {/* Period Start */}
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60 ml-1">
                  Activation Date
                </label>
                <div className="relative">
                  <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary opacity-40" />
                  <input
                    required
                    type="date"
                    value={periodStart}
                    onChange={(e) => setPeriodStart(e.target.value)}
                    className="w-full bg-[#020403] border border-white/10 rounded-2xl pl-10 pr-4 py-4 focus:outline-none focus:border-primary/50 transition-all text-xs font-bold text-white placeholder:text-muted-foreground/50"
                  />
                </div>
              </div>

              {/* Period End */}
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60 ml-1">
                  Expiration Date
                </label>
                <div className="relative">
                  <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary opacity-40" />
                  <input
                    required
                    type="date"
                    value={periodEnd}
                    onChange={(e) => setPeriodEnd(e.target.value)}
                    className="w-full bg-[#020403] border border-white/10 rounded-2xl pl-10 pr-4 py-4 focus:outline-none focus:border-primary/50 transition-all text-xs font-bold text-white placeholder:text-muted-foreground/50"
                  />
                </div>
              </div>
            </div>

            {/* Dynamic Categories */}
            <div className="space-y-4">
              <div className="flex justify-between items-center px-1">
                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60">
                  Category Allocations
                </label>
                <button
                  type="button"
                  onClick={addCategory}
                  className="text-primary text-[10px] font-black uppercase tracking-widest flex items-center gap-1 hover:opacity-80 transition-opacity"
                >
                  <Plus className="w-3 h-3" /> Add Sector
                </button>
              </div>

              <div className="space-y-3">
                {categories.map((category) => (
                  <div
                    key={category.id}
                    className="flex gap-3 animate-in fade-in slide-in-from-left-2 duration-300"
                  >
                    <input
                      required
                      placeholder="Category Name"
                      value={category.name}
                      onChange={(e) =>
                        updateCategory(category.id, "name", e.target.value)
                      }
                      className="flex-1 bg-[#020403] border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary/50 text-white placeholder:text-muted-foreground/50"
                    />
                    <div className="relative w-32">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-primary/60">
                        $
                      </span>
                      <input
                        required
                        type="number"
                        placeholder="Limit"
                        value={category.limit}
                        onChange={(e) =>
                          updateCategory(category.id, "limit", e.target.value)
                        }
                        className="w-full bg-[#020403] border border-white/10 rounded-xl pl-6 pr-3 py-3 text-sm focus:outline-none focus:border-primary/50 font-bold text-white placeholder:text-muted-foreground/50"
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeCategory(category.id)}
                      disabled={categories.length <= 1}
                      className="rounded-xl text-muted-foreground hover:text-red-400 hover:bg-red-500/10 shrink-0"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            <Button
              disabled={isSubmitting}
              type="submit"
              className="w-full h-14 rounded-2xl bg-primary text-[#020403] font-black uppercase tracking-widest hover:bg-primary/90 shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all disabled:opacity-50 gap-2 mt-4"
            >
              {isSubmitting ? (
                "Deploying Guard..."
              ) : (
                <>
                  <ShieldCheck className="w-5 h-5" />
                  Activate Budget
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
