import { type ElementType } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutGrid,
  BarChart3,
  Lock,
  Settings,
  LogOut,
  ShieldCheck,
  MessageSquare,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 bg-[#0A1210] border-r border-white/5 flex-col justify-between py-6 px-4 z-50 hidden md:flex font-sans">
      <div className="space-y-10">
        {/* Logo Area */}
        <div className="px-2 flex items-center gap-3 mt-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(16,185,129,0.3)]">
            <ShieldCheck className="w-5 h-5 text-[#020403] fill-current" />
          </div>
          <h1 className="text-lg font-bold text-white tracking-tight">
            Fiscal Guard
          </h1>
        </div>

        {/* Navigation */}
        <nav className="space-y-1">
          <SidebarItem
            icon={LayoutGrid}
            label="Command"
            active={isActive("/dashboard")}
            onClick={() => navigate("/dashboard")}
          />
          <SidebarItem
            icon={BarChart3}
            label="Insights"
            active={isActive("/insights")}
            onClick={() => navigate("/insights")}
          />
          <SidebarItem
            icon={MessageSquare}
            label="Chat"
            active={isActive("/chat")}
            onClick={() => navigate("/chat")}
          />
          <SidebarItem
            icon={Lock}
            label="Vault"
            active={isActive("/vault")}
            onClick={() => navigate("/vault")}
          />
          <SidebarItem
            icon={Settings}
            label="Setup"
            active={isActive("/setup")}
            onClick={() => navigate("/setup")}
          />
        </nav>
      </div>

      <div className="space-y-6 mb-2">
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 text-muted-foreground hover:text-white transition-colors group"
        >
          <LogOut className="w-5 h-5 opacity-70 group-hover:opacity-100" />
          <span className="text-sm font-medium">Sign Out</span>
        </button>

        <div className="bg-[#020403] rounded-xl p-3 flex items-center gap-3 border border-white/5 hover:bg-[#0F1A16] transition-colors cursor-pointer group">
          <img
            src={
              user?.picture ||
              `https://api.dicebear.com/7.x/notionists-neutral/svg?seed=${
                user?.name || user?.email?.split("@")[0] || "user"
              }`
            }
            alt={user?.name || "User"}
            className="w-10 h-10 rounded-full shadow-lg object-cover bg-muted border border-white/5"
          />
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-bold text-white truncate group-hover:text-primary transition-colors">
              {user?.name || "Guardian"}
            </span>
            <span className="text-[10px] font-medium text-muted-foreground truncate">
              {user?.email || "Protected Account"}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}

function SidebarItem({
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
        "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 relative outline-none group",
        active
          ? "bg-[#0F2922] text-primary"
          : "text-muted-foreground hover:text-white hover:bg-white/5",
      )}
    >
      {active && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
      )}
      <Icon
        className={cn(
          "w-5 h-5 transition-colors",
          active
            ? "text-primary"
            : "text-muted-foreground group-hover:text-white",
        )}
      />
      <span className={cn("text-sm font-medium", active && "font-bold")}>
        {label}
      </span>
    </button>
  );
}
