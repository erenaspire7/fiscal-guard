import React, { useState } from "react";
import { X, Target, Calendar, Award } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface AddGoalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  token: string | null;
}

export default function AddGoalModal({
  isOpen,
  onClose,
  onSuccess,
  token,
}: AddGoalModalProps) {
  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [deadline, setDeadline] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/goals`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            goal_name: name,
            target_amount: parseFloat(target),
            priority,
            deadline: deadline || null,
          }),
        }
      );

      if (response.ok) {
        onSuccess();
        onClose();
        setName("");
        setTarget("");
        setDeadline("");
      }
    } catch (error) {
      console.error("Failed to create goal:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-300">
      <Card className="w-full max-w-md bg-card/90 border-white/10 shadow-2xl rounded-[32px] overflow-hidden animate-in slide-in-from-bottom-8 duration-500">
        <div className="absolute top-4 right-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="rounded-full hover:bg-white/5"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        <CardContent className="p-8 space-y-8">
          <div className="space-y-2">
            <div className="w-12 h-12 bg-primary/20 rounded-2xl flex items-center justify-center mb-4">
              <Target className="w-6 h-6 text-primary shadow-primary-glow" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight">New Asset Goal</h2>
            <p className="text-sm text-muted-foreground">
              Define a new target for the Fiscal Guard to protect.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              {/* Goal Name */}
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60 ml-1">
                  Goal Name
                </label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Home Downpayment"
                  className="w-full bg-background/50 border border-white/5 rounded-2xl px-4 py-4 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all font-medium"
                />
              </div>

              {/* Target Amount */}
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60 ml-1">
                  Target Amount ($)
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-primary opacity-60">
                    $
                  </span>
                  <input
                    required
                    type="number"
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    placeholder="5000"
                    className="w-full bg-background/50 border border-white/5 rounded-2xl pl-8 pr-4 py-4 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all font-bold"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Deadline */}
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60 ml-1">
                    Deadline
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary opacity-40" />
                    <input
                      type="date"
                      value={deadline}
                      onChange={(e) => setDeadline(e.target.value)}
                      className="w-full bg-background/50 border border-white/5 rounded-2xl pl-10 pr-4 py-4 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all text-xs font-bold"
                    />
                  </div>
                </div>

                {/* Priority */}
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60 ml-1">
                    Priority
                  </label>
                  <select
                    value={priority}
                    onChange={(e) =>
                      setPriority(e.target.value as "low" | "medium" | "high")
                    }
                    className="w-full bg-background/50 border border-white/5 rounded-2xl px-4 py-4 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all text-xs font-bold appearance-none"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>
            </div>

            <Button
              disabled={isSubmitting}
              type="submit"
              className="w-full h-14 rounded-2xl bg-primary text-background font-black uppercase tracking-widest hover:bg-primary/90 shadow-primary-glow transition-all disabled:opacity-50 gap-2"
            >
              {isSubmitting ? (
                "Initializing..."
              ) : (
                <>
                  <Award className="w-5 h-5" />
                  Establish Goal
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
