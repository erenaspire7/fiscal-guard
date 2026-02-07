import React, { useState } from "react";
import { Target, Loader2 } from "lucide-react";
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
  const [deadline, setDeadline] = useState<Date>();
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(`${env.apiUrl}/goals`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          goal_name: name,
          target_amount: parseFloat(target),
          priority,
          deadline: deadline ? deadline.toISOString().split("T")[0] : null,
        }),
      });

      if (response.ok) {
        onSuccess();
        onClose();
        setName("");
        setTarget("");
        setDeadline(undefined);
      }
    } catch (error) {
      console.error("Failed to create goal:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#040d07] border-white/5 text-white sm:max-w-md overflow-x-hidden shadow-xl">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-4 border border-emerald-500/20">
              <Target className="w-6 h-6 text-emerald-500 fill-emerald-500/20" />
            </div>
            <DialogTitle className="text-2xl font-semibold tracking-tight text-white">
              New Asset Goal
            </DialogTitle>
            <DialogDescription className="text-sm text-gray-400">
              Define a new target for the Fiscal Guard to protect.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 mt-4">
            <div className="space-y-4">
              {/* Goal Name */}
              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-300 ml-1">
                  Goal Name
                </Label>
                <Input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Home Downpayment"
                  className="w-full bg-[#010402] border-white/5 rounded-xl px-4 py-4 font-medium text-white placeholder:text-gray-500 shadow-inner"
                />
              </div>

              {/* Target Amount */}
              <div className="space-y-2">
                <Label className="text-sm font-medium text-gray-300 ml-1">
                  Target Amount ($)
                </Label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-primary opacity-60">
                    $
                  </span>
                  <Input
                    required
                    type="number"
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    placeholder="5000"
                    className="w-full bg-[#010402] border-white/5 rounded-xl pl-8 pr-4 py-4 font-bold text-white placeholder:text-gray-500 shadow-inner"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Deadline */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-gray-300 ml-1">
                    Deadline
                  </Label>
                  <DatePicker
                    date={deadline}
                    onDateChange={setDeadline}
                    placeholder="Select deadline"
                    className="w-full bg-[#010402] border-white/5 rounded-xl px-4 py-4 text-xs font-bold text-white shadow-inner h-auto"
                  />
                </div>

                {/* Priority */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-gray-300 ml-1">
                    Priority
                  </Label>
                  <select
                    value={priority}
                    onChange={(e) =>
                      setPriority(e.target.value as "low" | "medium" | "high")
                    }
                    className="w-full bg-[#010402] border border-white/5 rounded-xl px-4 py-4 focus:outline-none focus:border-primary/50 transition-all text-xs font-bold appearance-none text-white shadow-inner"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
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
                    Creating goal...
                  </>
                ) : (
                  "Create Goal"
                )}
              </Button>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
