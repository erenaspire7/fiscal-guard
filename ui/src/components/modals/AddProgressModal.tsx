import React, { useState } from "react";
import { TrendingUp, Loader2 } from "lucide-react";
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
import { env } from "@/config/env";

interface AddProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  token: string | null;
  goalId: string;
  goalName: string;
}

export default function AddProgressModal({
  isOpen,
  onClose,
  onSuccess,
  token,
  goalId,
  goalName,
}: AddProgressModalProps) {
  const [amount, setAmount] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !amount) return;

    const amountValue = parseFloat(amount);
    if (isNaN(amountValue) || amountValue <= 0) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(
        `${env.apiUrl}/goals/${goalId}/progress`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ amount: amountValue }),
        },
      );

      if (response.ok) {
        onSuccess();
        onClose();
        setAmount("");
      }
    } catch (error) {
      console.error("Failed to add progress:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    onClose();
    setAmount("");
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <form onSubmit={handleSubmit}>
        <DialogContent className="bg-[#040d07] border-white/5 text-white sm:max-w-md overflow-x-hidden shadow-xl">
          <DialogHeader>
            <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-4 border border-emerald-500/20">
              <TrendingUp className="w-6 h-6 text-emerald-500" />
            </div>
            <DialogTitle className="text-2xl font-semibold tracking-tight text-white">
              Add Progress
            </DialogTitle>
            <DialogDescription className="text-sm text-gray-400">
              Contributing to{" "}
              <span className="text-emerald-500 font-semibold">{goalName}</span>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-gray-300 ml-1">
                Amount ($)
              </Label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-xl font-bold text-gray-500">
                  $
                </span>
                <Input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  required
                  autoFocus
                  className="w-full bg-[#010402] border-white/5 rounded-xl py-4 pl-10 pr-4 text-xl font-bold text-white placeholder:text-gray-500 shadow-inner focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
                />
              </div>
              {amount && parseFloat(amount) > 0 && (
                <p className="text-xs text-emerald-500/60">
                  This will be added to your goal savings
                </p>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button
                type="button"
                onClick={handleClose}
                variant="outline"
                className="border-white/10 hover:bg-white/5 hover:text-white text-white font-medium py-3 px-6 rounded-xl transition-all text-sm"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!amount || isSubmitting || parseFloat(amount) <= 0}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-900/20 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Adding...
                  </>
                ) : (
                  "Add Progress"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </form>
    </Dialog>
  );
}
