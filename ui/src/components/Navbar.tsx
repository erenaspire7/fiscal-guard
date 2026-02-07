import { type ElementType } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { LayoutDashboard, Shield, Wallet, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-[#020804]/90 backdrop-blur-xl border-t border-white/5 px-6 py-4 flex justify-around items-center z-50">
      <NavItem
        icon={LayoutDashboard}
        label="Dashboard"
        active={isActive("/dashboard")}
        onClick={() => navigate("/dashboard")}
      />
      <NavItem
        icon={Shield}
        label="Guard"
        active={isActive("/chat")}
        onClick={() => navigate("/chat")}
      />
      <NavItem
        icon={Wallet}
        label="Vault"
        active={isActive("/vault")}
        onClick={() => navigate("/vault")}
      />
      <NavItem
        icon={Settings2}
        label="Setup"
        active={isActive("/setup")}
        onClick={() => navigate("/setup")}
      />
    </nav>
  );
}

function NavItem({
  icon: Icon,
  label,
  active = false,
  onClick,
}: {
  icon: ElementType;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex flex-col items-center gap-1.5 transition-all relative outline-none",
        active
          ? "opacity-100 text-emerald-500"
          : "opacity-40 text-gray-400 hover:opacity-70",
      )}
    >
      <Icon
        className={cn("w-5 h-5 transition-transform", active && "scale-110")}
      />
      <span className="text-[9px] font-bold uppercase tracking-widest">
        {label}
      </span>
      {active && (
        <div className="absolute -bottom-1 w-1 h-1 bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
      )}
    </button>
  );
}
