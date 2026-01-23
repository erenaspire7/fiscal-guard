import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  ArrowLeft,
  Megaphone,
  Save,
  MessageSquare,
  Shield,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function AgentConfiguration() {
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [strictness, setStrictness] = useState(75);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (user) {
      // Map backend values back to UI strictness (0-100)
      const level = (user as any).strictness_level || 5;
      const persona = (user as any).persona_tone || "balanced";

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

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/users/me`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            persona_tone,
            strictness_level,
          }),
        },
      );

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
    <div className="min-h-screen bg-background text-foreground font-sans pb-32">
      {/* Header */}
      <header className="px-6 py-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(-1)}
            className="rounded-full hover:bg-white/5 -ml-2"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-primary opacity-80">
              AI Tuning
            </p>
            <h1 className="text-2xl font-bold tracking-tight">Agent Config</h1>
          </div>
        </div>
        <Button
          size="icon"
          onClick={handleSave}
          disabled={isSaving}
          className={cn(
            "rounded-xl bg-card border border-white/5 text-primary shadow-lg w-10 h-10 transition-all",
            isSaving && "opacity-50",
          )}
        >
          <Save className={cn("w-5 h-5", isSaving && "animate-pulse")} />
        </Button>
      </header>

      <main className="px-6 space-y-10">
        {/* Persuasion Tone */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 px-1">
            <Megaphone className="w-5 h-5 text-primary" />
            <h3 className="text-xl font-bold tracking-tight">
              Persuasion Tone
            </h3>
          </div>

          <Card className="bg-card/40 border-none rounded-[32px] overflow-hidden">
            <CardContent className="p-6 space-y-8">
              <div className="flex justify-between items-end">
                <div className="space-y-1">
                  <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-50">
                    Selected Mode
                  </p>
                  <p className="text-lg font-bold">
                    {getIntensityLabel(strictness)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-primary font-bold text-glow">
                    {strictness}% Intensity
                  </p>
                </div>
              </div>

              {/* Custom Slider */}
              <div className="relative py-4">
                <div className="h-1.5 w-full bg-background rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary shadow-primary-glow transition-all duration-300"
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
                <div className="flex justify-between mt-6 px-1">
                  {[0, 25, 50, 75, 100].map((val) => (
                    <div
                      key={val}
                      className={cn(
                        "w-1.5 h-1.5 rounded-full transition-colors",
                        strictness >= val
                          ? "bg-primary shadow-primary-glow"
                          : "bg-muted",
                      )}
                    />
                  ))}
                </div>
                <div className="flex justify-between mt-3 -mx-2">
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
                        "text-[7px] font-black uppercase tracking-widest w-12 text-center transition-colors duration-300",
                        strictness === item.val
                          ? "text-primary text-glow opacity-100"
                          : "text-muted-foreground opacity-30",
                      )}
                    >
                      {item.label}
                    </span>
                  ))}
                </div>
              </div>

              {/* Agent Preview Box */}
              <div className="bg-background/60 rounded-[24px] p-5 border border-white/5 relative">
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare
                    className="w-3 h-3 text-primary"
                    fill="currentColor"
                  />
                  <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60">
                    Agent Preview: $200 Purchase
                  </span>
                </div>
                <p className="text-sm italic leading-relaxed text-foreground/90 font-medium">
                  "{getAgentPreview(strictness)}"
                </p>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Guardrail Rules */}
        <section className="space-y-4">
          <div className="flex items-center gap-3 px-1">
            <Shield className="w-5 h-5 text-primary" />
            <h3 className="text-xl font-bold tracking-tight">
              Guardrail Rules
            </h3>
          </div>

          <div className="bg-card/40 rounded-[28px] overflow-hidden divide-y divide-white/5">
            <button className="w-full flex items-center justify-between p-6 hover:bg-white/5 transition-colors text-left outline-none">
              <div className="space-y-1">
                <p className="font-bold text-sm">Flag large purchases</p>
                <p className="text-[11px] text-muted-foreground font-medium opacity-60">
                  Threshold for mandatory interception
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-primary font-bold text-sm text-glow">
                  $500
                </span>
                <ChevronRight className="w-4 h-4 text-muted-foreground opacity-40" />
              </div>
            </button>

            <button className="w-full flex items-center justify-between p-6 hover:bg-white/5 transition-colors text-left outline-none">
              <div className="space-y-1">
                <p className="font-bold text-sm">Daily spending cap</p>
                <p className="text-[11px] text-muted-foreground font-medium opacity-60">
                  Daily alert trigger point
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-primary font-bold text-sm text-glow">
                  $150
                </span>
                <ChevronRight className="w-4 h-4 text-muted-foreground opacity-40" />
              </div>
            </button>
          </div>
        </section>
      </main>

      <Navbar />
    </div>
  );
}
