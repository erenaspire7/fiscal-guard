import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

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
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#040d07] border-white/5 text-white sm:max-w-sm text-center overflow-x-hidden shadow-xl">
        <div className="mx-auto w-16 h-16 bg-red-500/10 rounded-xl flex items-center justify-center mb-4 border border-red-500/20">
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>

        <DialogHeader className="text-center">
          <DialogTitle className="text-xl font-semibold tracking-tight text-white">
            {title}
          </DialogTitle>
          <DialogDescription className="text-sm text-gray-400 leading-relaxed">
            {description}
          </DialogDescription>
        </DialogHeader>

        <div className="flex justify-end gap-3 mt-6">
          <Button
            variant="outline"
            onClick={onClose}
            className="border-white/10 hover:bg-white/5 hover:text-white text-white font-medium py-3 px-6 rounded-xl transition-all text-sm"
          >
            Cancel
          </Button>
          <Button
            disabled={isDeleting}
            onClick={onConfirm}
            className="bg-red-600 hover:bg-red-500 text-white font-medium py-3 px-6 rounded-xl transition-all shadow-lg disabled:opacity-70 disabled:cursor-not-allowed text-sm"
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
