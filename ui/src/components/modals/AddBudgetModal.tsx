import React, { useState } from "react";
import { Wallet, Plus, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DatePicker } from "@/components/ui/date-picker";
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
  const [periodStart, setPeriodStart] = useState<Date>();
  const [periodEnd, setPeriodEnd] = useState<Date>();
  const [categories, setCategories] = useState<CategoryEntry[]>([
    {
      id: Math.random().toString(36).substr(2, 9),
      name: "Groceries",
      limit: "",
    },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
          period_start: periodStart?.toISOString().split("T")[0],
          period_end: periodEnd?.toISOString().split("T")[0],
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
    <Dialog open={isOpen} onOpenChange={onClose}>
      <form onSubmit={handleSubmit}>
        <DialogContent className="bg-[#040d07] border-white/5 text-white sm:max-w-xl max-h-[90vh] overflow-y-auto overflow-x-hidden shadow-2xl">
          <DialogHeader>
            <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-4 border border-emerald-500/20">
              <Wallet className="w-6 h-6 text-emerald-500 fill-emerald-500/20" />
            </div>
            <DialogTitle className="text-2xl font-semibold tracking-tight text-white">
              Establish Budget
            </DialogTitle>
            <DialogDescription className="text-sm text-gray-400">
              Define the boundaries of your financial guard for this period.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 mt-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Budget Name */}
              <div className="space-y-2 sm:col-span-2">
                <Label className="text-sm font-medium text-gray-300 ml-1">
                  Budget Reference Name
                </Label>
                <Input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Q1 2026 Strategic Plan"
                  className="w-full bg-[#010402] border-white/5 rounded-xl px-4 py-3 text-sm font-medium text-white placeholder:text-gray-500 shadow-inner focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
                />
              </div>

              {/* Total Limit */}
              <div className="space-y-2 sm:col-span-2">
                <Label className="text-sm font-medium text-gray-300 ml-1">
                  Total Monthly Limit ($)
                </Label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-primary opacity-60">
                    $
                  </span>
                  <Input
                    required
                    type="number"
                    value={totalMonthly}
                    onChange={(e) => setTotalMonthly(e.target.value)}
                    placeholder="4000"
                    className="w-full bg-[#010402] border-white/5 rounded-xl pl-8 pr-4 py-4 font-bold text-xl text-white placeholder:text-gray-500 shadow-inner"
                  />
                </div>
              </div>

              {/* Period Start */}
              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-300 ml-1">
                  Activation Date
                </Label>
                <DatePicker
                  date={periodStart}
                  onDateChange={setPeriodStart}
                  placeholder="Select start date"
                  className="w-full bg-[#010402] border-white/5 rounded-xl px-4 py-4 text-xs font-bold text-white shadow-inner h-auto"
                />
              </div>

              {/* Period End */}
              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-300 ml-1">
                  Expiration Date
                </Label>
                <DatePicker
                  date={periodEnd}
                  onDateChange={setPeriodEnd}
                  placeholder="Select end date"
                  className="w-full bg-[#010402] border-white/5 rounded-xl px-4 py-4 text-xs font-bold text-white shadow-inner h-auto"
                />
              </div>
            </div>

            {/* Dynamic Categories */}
            <div className="space-y-4">
              <div className="flex justify-between items-center px-1">
                <Label className="text-sm font-medium text-gray-300">
                  Category Allocations
                </Label>
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
                    <Input
                      required
                      placeholder="Category Name"
                      value={category.name}
                      onChange={(e) =>
                        updateCategory(category.id, "name", e.target.value)
                      }
                      className="flex-1 bg-[#010402] border-white/5 rounded-xl px-4 py-3 text-sm text-white placeholder:text-gray-500 shadow-inner"
                    />
                    <div className="relative w-32">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-primary/60">
                        $
                      </span>
                      <Input
                        required
                        type="number"
                        placeholder="Limit"
                        value={category.limit}
                        onChange={(e) =>
                          updateCategory(category.id, "limit", e.target.value)
                        }
                        className="w-full bg-[#010402] border-white/5 rounded-xl pl-6 pr-3 py-3 text-sm font-bold text-white placeholder:text-gray-500 shadow-inner"
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

            <div className="flex justify-end">
              <Button
                disabled={isSubmitting}
                type="submit"
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-900/20 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating budget...
                  </>
                ) : (
                  "Create Budget"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </form>
    </Dialog>
  );
}
