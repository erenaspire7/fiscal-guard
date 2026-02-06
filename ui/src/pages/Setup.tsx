import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
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
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";

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
        // TODO: Implement versioning
        { icon: Info, label: "Help & Support", value: "v1.0.0" },
      ],
    },
  ];

  return (
    <div
      className={cn(
        "min-h-screen text-white font-sans pb-32 md:pb-0 md:pl-64 transition-all duration-300",
        ThemeBackgrounds[DEFAULT_THEME],
      )}
    >
      <Sidebar />

      <main className="px-6 py-8 md:p-12 max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-500 opacity-80">
              Preferences
            </p>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              Setup
            </h1>
          </div>
        </header>

        {/* User Profile Summary Card */}
        <section className="bg-[#040d07] border border-white/5 rounded-[32px] p-6 md:p-8 relative overflow-hidden group shadow-xl">
          <div className="absolute top-0 right-0 p-32 bg-emerald-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />

          <div className="flex flex-col md:flex-row items-start md:items-center gap-6 relative z-10">
            <div className="relative shrink-0">
              <div className="absolute inset-0 bg-emerald-500/20 blur-xl rounded-full" />
              <img
                src={
                  user?.picture ||
                  `https://api.dicebear.com/7.x/notionists-neutral/svg?seed=${
                    user?.name || user?.email?.split("@")[0] || "user"
                  }`
                }
                alt="Profile"
                className="relative w-20 h-20 md:w-24 md:h-24 rounded-3xl border-2 border-white/10 shadow-2xl object-cover"
              />
              <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full border-[3px] border-[#040d07] flex items-center justify-center">
                <CheckCircle2 className="w-3 h-3 text-[#020804]" />
              </div>
            </div>

            <div className="flex-1 space-y-2">
              <div>
                <h2 className="text-2xl md:text-3xl font-bold leading-tight text-white">
                  {user?.name || user?.email?.split("@")[0] || "User"}
                </h2>
                <p className="text-sm text-emerald-500 font-bold opacity-90 flex items-center gap-2">
                  {/*TODO: Change*/}
                  {/*Premium Guard Member
                  <span className="w-1 h-1 rounded-full bg-white/30" />*/}
                  <span className="text-gray-500 font-normal">Since 2024</span>
                </p>
              </div>
              <div className="flex gap-3 pt-2">
                <button className="px-4 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-white text-xs font-bold rounded-xl border border-white/5 transition-colors">
                  Edit Profile
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Settings Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {menuGroups.map((group, i) => (
            <section key={i} className="space-y-4">
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 px-1 opacity-50 ml-2">
                {group.label}
              </h3>
              <div className="bg-[#040d07] border border-white/5 rounded-[32px] overflow-hidden shadow-xl">
                {group.items.map((item, j) => (
                  <button
                    key={j}
                    onClick={item.onClick}
                    className={cn(
                      "w-full flex items-center gap-5 p-6 hover:bg-emerald-500/5 transition-all text-left outline-none group border-b border-white/5 last:border-0",
                    )}
                  >
                    <div className="w-12 h-12 bg-emerald-500/10 rounded-2xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-300">
                      <item.icon className="w-6 h-6 text-emerald-500" />
                    </div>
                    <div className="flex-1">
                      <p className="font-bold text-base text-white group-hover:text-emerald-500 transition-colors">
                        {item.label}
                      </p>
                      <p className="text-xs text-gray-500 font-medium mt-1 opacity-60">
                        {item.value}
                      </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-500 opacity-20 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                  </button>
                ))}
              </div>
            </section>
          ))}
        </div>

        {/* Danger Zone / Mobile Sign Out */}
        <div className="pt-8 md:hidden">
          <Button
            onClick={logout}
            variant="outline"
            className="w-full h-14 rounded-2xl border-red-500/20 bg-red-500/5 text-red-400 hover:bg-red-500/10 hover:border-red-500/30 gap-3 font-bold text-sm"
          >
            <LogOut className="w-5 h-5" />
            Sign Out of Fiscal Guard
          </Button>
          <p className="text-center text-[10px] text-gray-500 mt-8 font-bold uppercase tracking-widest opacity-30">
            Powered by Gemini & Opik
          </p>
        </div>
      </main>

      <div className="md:hidden">
        <Navbar />
      </div>
    </div>
  );
}
