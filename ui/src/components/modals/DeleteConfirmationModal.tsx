import React from "react";
import { AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface DeleteConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  isDeleting?: boolean;
}

export default function DeleteConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  isDeleting = false,
}: DeleteConfirmationModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-300">
      <Card className="w-full max-w-sm bg-card/90 border-white/10 shadow-2xl rounded-[32px] overflow-hidden animate-in zoom-in-95 duration-300">
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

        <CardContent className="p-8 text-center space-y-6">
          <div className="mx-auto w-16 h-16 bg-destructive/20 rounded-2xl flex items-center justify-center mb-2">
            <AlertTriangle className="w-8 h-8 text-destructive animate-pulse" />
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold tracking-tight">{title}</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {description}
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-2">
            <Button
              disabled={isDeleting}
              onClick={onConfirm}
              className={cn(
                "w-full h-12 rounded-2xl bg-destructive text-white font-bold uppercase tracking-widest hover:bg-destructive/90 transition-all",
                isDeleting && "opacity-50"
              )}
            >
              {isDeleting ? "Deauthorizing..." : "Confirm Deletion"}
            </Button>
            <Button
              variant="ghost"
              onClick={onClose}
              className="w-full h-12 rounded-2xl font-bold uppercase tracking-widest text-muted-foreground hover:bg-white/5"
            >
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
