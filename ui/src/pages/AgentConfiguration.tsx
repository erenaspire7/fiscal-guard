import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { env } from "@/config/env";
import {
  ArrowLeft,
  Megaphone,
  Save,
  MessageSquare,
  Shield,
  ChevronRight,
  Bot,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";

export default function AgentConfiguration() {
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [strictness, setStrictness] = useState(75);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (user) {
      // Map backend values back to UI strictness (0-100)
      const level = user.strictness_level || 5;
      const persona = user.persona_tone || "balanced";

      if (persona === "financial_monk") {
        setStrictness(level >= 9 ? 100 : 75);
      } else if (persona === "gentle") {
        setStrictness(level <= 2 ? 0 : 25);
      } else {
        setStrictness(50);
      }
    }
  }, [user]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      let persona_tone = "balanced";
      if (strictness <= 25) persona_tone = "gentle";
      else if (strictness >= 75) persona_tone = "financial_monk";

      const strictness_level = Math.max(
        1,
        Math.min(10, Math.round(strictness / 10) + 1),
      );

      const response = await fetch(`${env.apiUrl}/users/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          persona_tone,
          strictness_level,
        }),
      });

      if (!response.ok) throw new Error("Failed to save settings");
    } catch (error) {
      console.error("Save error:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const getIntensityLabel = (val: number) => {
    if (val <= 25) return "Gentle Advisor";
    if (val <= 50) return "Balanced";
    if (val <= 75) return "Strict Guardian";
    return "Financial Monk";
  };

  const getAgentPreview = (val: number) => {
    if (val <= 25)
      return "I noticed this $200 purchase. It's a bit high for your current trend, but if it's important, just make sure to adjust next week's grocery budget.";
    if (val <= 50)
      return "This $200 purchase will put you 15% over your flexible budget. I recommend waiting 48 hours to see if you still feel it's necessary.";
    if (val <= 75)
      return "This request for $200 exceeds your remaining flexible budget by 42%. Given your current trend, this will delay your 'Home Downpayment' goal by 3 weeks. Permission to spend is withheld until next salary cycle.";
    return "Spending request denied. This $200 purchase is classified as non-essential and violates your 'Zero-Waste' policy. Your goal of financial freedom requires absolute discipline this month.";
  };

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
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(-1)}
              className="rounded-full hover:bg-white/10 -ml-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </Button>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-500 opacity-80">
                AI Tuning
              </p>
              <h1 className="text-3xl font-bold tracking-tight text-white">
                Agent Config
              </h1>
            </div>
          </div>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className={cn(
              "rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg shadow-emerald-900/20 px-6 transition-all font-bold gap-2",
              isSaving && "opacity-50",
            )}
          >
            <Save className={cn("w-4 h-4", isSaving && "animate-pulse")} />
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Left/Top Column: Persuasion Tone (Takes up more space) */}
          <section className="lg:col-span-3 space-y-6">
            <div className="flex items-center gap-3 px-1">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <Megaphone className="w-4 h-4 text-emerald-500" />
              </div>
              <h3 className="text-xl font-bold tracking-tight text-white">
                Persuasion Tone
              </h3>
            </div>

            <Card className="bg-[#040d07] border border-white/5 rounded-[32px] overflow-hidden shadow-xl">
              <CardContent className="p-8 space-y-10">
                <div className="flex justify-between items-end">
                  <div className="space-y-2">
                    <p className="text-[10px] font-black uppercase tracking-widest text-gray-500 opacity-50">
                      Selected Mode
                    </p>
                    <p className="text-2xl font-bold text-white">
                      {getIntensityLabel(strictness)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-emerald-500 font-bold text-xl drop-shadow-[0_0_8px_rgba(16,185,129,0.6)]">
                      {strictness}% Intensity
                    </p>
                  </div>
                </div>

                {/* Custom Slider */}
                <div className="relative py-6 px-2">
                  {/* Track Background */}
                  <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)] transition-all duration-300"
                      style={{ width: `${strictness}%` }}
                    />
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="25"
                    value={strictness}
                    onChange={(e) => setStrictness(parseInt(e.target.value))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  />
                  {/* Ticks */}
                  <div className="flex justify-between mt-8 -mx-1.5">
                    {[0, 25, 50, 75, 100].map((val) => (
                      <div
                        key={val}
                        className="flex flex-col items-center gap-3 group"
                      >
                        <div
                          className={cn(
                            "w-3 h-3 rounded-full transition-all duration-300 border border-transparent",
                            strictness >= val
                              ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)] scale-110"
                              : "bg-[#0a0f0c] border-white/10 group-hover:bg-white/10",
                          )}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between mt-2 -mx-4">
                    {[
                      { val: 0, label: "Gentle" },
                      { val: 25, label: "Balanced" },
                      { val: 50, label: "Strict" },
                      { val: 75, label: "Monk" },
                      { val: 100, label: "Zenith" },
                    ].map((item) => (
                      <span
                        key={item.val}
                        className={cn(
                          "text-[9px] font-black uppercase tracking-widest w-16 text-center transition-colors duration-300",
                          strictness === item.val
                            ? "text-emerald-500 opacity-100"
                            : "text-gray-500 opacity-30",
                        )}
                      >
                        {item.label}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Agent Preview Box */}
                <div className="bg-[#020804] rounded-[24px] p-6 border border-white/5 relative group hover:border-emerald-500/20 transition-all shadow-lg">
                  <div className="absolute top-0 right-0 p-20 bg-emerald-500/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />
                  <div className="flex items-center gap-3 mb-4 relative z-10">
                    <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center">
                      <Bot className="w-4 h-4 text-emerald-500" />
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 opacity-60">
                      Agent Preview: $200 Purchase
                    </span>
                  </div>
                  <div className="relative z-10 pl-11">
                    <div className="relative">
                      <MessageSquare
                        className="w-4 h-4 text-emerald-500 absolute -left-6 top-1 opacity-50"
                        fill="currentColor"
                      />
                      <p className="text-base italic leading-relaxed text-white/90 font-medium">
                        "{getAgentPreview(strictness)}"
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Right Column: Guardrail Rules */}
          {/*<section className="lg:col-span-2 space-y-6">
            <div className="flex items-center gap-3 px-1">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <Shield className="w-4 h-4 text-emerald-500" />
              </div>
              <h3 className="text-xl font-bold tracking-tight text-white">
                Guardrail Rules
              </h3>
            </div>

            <div className="bg-[#040d07] border border-white/5 rounded-[28px] overflow-hidden divide-y divide-white/5 shadow-xl h-full flex flex-col">
              <button className="w-full flex items-center justify-between p-6 hover:bg-emerald-500/5 transition-colors text-left outline-none group flex-1">
                <div className="space-y-1">
                  <p className="font-bold text-white group-hover:text-emerald-500 transition-colors">
                    Flag large purchases
                  </p>
                  <p className="text-xs text-gray-500 font-medium opacity-60">
                    Threshold for mandatory interception
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-emerald-500 font-bold text-base drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]">
                    $500
                  </span>
                  <ChevronRight className="w-5 h-5 text-gray-500 opacity-20 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                </div>
              </button>

              <button className="w-full flex items-center justify-between p-6 hover:bg-emerald-500/5 transition-colors text-left outline-none group flex-1">
                <div className="space-y-1">
                  <p className="font-bold text-white group-hover:text-emerald-500 transition-colors">
                    Daily spending cap
                  </p>
                  <p className="text-xs text-gray-500 font-medium opacity-60">
                    Daily alert trigger point
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-emerald-500 font-bold text-base drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]">
                    $150
                  </span>
                  <ChevronRight className="w-5 h-5 text-gray-500 opacity-20 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                </div>
              </button>

              <button className="w-full flex items-center justify-between p-6 hover:bg-emerald-500/5 transition-colors text-left outline-none group flex-1">
                <div className="space-y-1">
                  <p className="font-bold text-white group-hover:text-emerald-500 transition-colors">
                    Recurring Audit
                  </p>
                  <p className="text-xs text-gray-500 font-medium opacity-60">
                    Review subscription charges
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-emerald-500 font-bold text-xs uppercase tracking-wider bg-emerald-500/10 px-2 py-1 rounded">
                    Monthly
                  </span>
                  <ChevronRight className="w-5 h-5 text-gray-500 opacity-20 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                </div>
              </button>
            </div>
          </section>*/}
        </div>
      </main>

      <div className="md:hidden">
        <Navbar />
      </div>
    </div>
  );
}
