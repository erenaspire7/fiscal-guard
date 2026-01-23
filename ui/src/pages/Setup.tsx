import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import {
  User,
  Bell,
  Lock,
  Shield,
  CreditCard,
  LogOut,
  ChevronRight,
  Moon,
  Smartphone,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function Setup() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const menuGroups = [
    {
      label: "Account",
      items: [
        { icon: User, label: "Personal Information", value: "Edit profile" },
        { icon: CreditCard, label: "Linked Accounts", value: "3 Active" },
        { icon: Lock, label: "Security & Privacy", value: "2FA Enabled" },
      ],
    },
    {
      label: "Guardian Logic",
      items: [
        {
          icon: Shield,
          label: "Guard Strictness",
          value: "Strict Guardian",
          onClick: () => navigate("/setup/agent"),
        },
        { icon: Bell, label: "Notifications", value: "Smart Alerts" },
        { icon: Moon, label: "Display Theme", value: "Dark Green" },
      ],
    },
    {
      label: "App",
      items: [
        { icon: Smartphone, label: "Data Export", value: "CSV/JSON" },
        { icon: Info, label: "Help & Support", value: "v1.0.4" },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans pb-32">
      {/* Header */}
      <header className="px-6 py-8">
        <p className="text-[10px] font-bold uppercase tracking-wider text-primary opacity-80">
          Preferences
        </p>
        <h1 className="text-3xl font-bold tracking-tight">Setup</h1>
      </header>

      <main className="px-6 space-y-8">
        {/* User Profile Summary - Refined horizontal style */}
        <section className="flex items-center gap-5 p-2 mb-4">
          <div className="relative shrink-0">
            <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
            <img
              src={
                user?.picture ||
                `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || user?.email?.split("@")[0] || "user"}`
              }
              alt="Profile"
              className="relative w-16 h-16 rounded-2xl border-2 border-background shadow-xl"
            />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold leading-tight">
              {user?.name || user?.email?.split("@")[0] || "User"}
            </h2>
            <p className="text-xs text-muted-foreground font-medium opacity-60">
              Premium Guard Member
            </p>
          </div>
          <Button variant="ghost" size="icon" className="opacity-40">
            <ChevronRight className="w-5 h-5" />
          </Button>
        </section>

        {/* Settings Groups */}
        <div className="space-y-8">
          {menuGroups.map((group, i) => (
            <section key={i} className="space-y-3">
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground px-1 opacity-50">
                {group.label}
              </h3>
              <div className="bg-card/40 rounded-[28px] overflow-hidden divide-y divide-white/5">
                {group.items.map((item, j) => (
                  <button
                    key={j}
                    onClick={item.onClick}
                    className={cn(
                      "w-full flex items-center gap-4 p-5 hover:bg-white/5 active:bg-white/10 transition-colors text-left outline-none",
                    )}
                  >
                    <div className="w-10 h-10 bg-background/40 rounded-xl flex items-center justify-center shrink-0">
                      <item.icon className="w-5 h-5 text-primary/70" />
                    </div>
                    <div className="flex-1">
                      <p className="font-bold text-sm leading-none">
                        {item.label}
                      </p>
                      <p className="text-[11px] text-muted-foreground font-medium mt-1.5 opacity-70">
                        {item.value}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground opacity-40" />
                  </button>
                ))}
              </div>
            </section>
          ))}
        </div>

        {/* Danger Zone */}
        <div className="pt-4">
          <Button
            onClick={logout}
            variant="outline"
            className="w-full h-14 rounded-2xl border-red-500/20 bg-red-500/5 text-red-400 hover:bg-red-500/10 hover:border-red-500/30 gap-3 font-bold text-sm"
          >
            <LogOut className="w-5 h-5" />
            Sign Out of Fiscal Guard
          </Button>
          <p className="text-center text-[10px] text-muted-foreground mt-8 font-bold uppercase tracking-widest opacity-30">
            Powered by Strands & Opik
          </p>
        </div>
      </main>

      <Navbar />
    </div>
  );
}
