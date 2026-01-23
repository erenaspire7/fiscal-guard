import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { useChat } from "@/hooks/useChat";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Send, Shield, User, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AgentChat() {
  const navigate = useNavigate();
  const { messages, sendMessage, isLoading } = useChat();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const text = input;
    setInput("");
    await sendMessage(text);
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground font-sans max-w-md mx-auto relative overflow-hidden">
      {/* Sticky Header */}
      <header className="p-4 flex items-center gap-4 bg-background/80 backdrop-blur-xl border-b border-white/5 z-10">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(-1)}
          className="rounded-full hover:bg-white/5"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center shadow-primary-glow">
            <Shield className="w-6 h-6 text-background" fill="currentColor" />
          </div>
          <div>
            <h1 className="font-bold leading-tight">Fiscal Guard Agent</h1>
            <p className="text-[10px] uppercase tracking-widest text-primary font-bold opacity-80">
              Active Session
            </p>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-5 space-y-6 scroll-smooth pb-32"
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-60">
            <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-2">
              <Shield className="w-8 h-8 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium px-12">
              Welcome back. Tell me about a purchase you're considering, and
              I'll help you decide if it aligns with your goals.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex w-full gap-3",
              msg.role === "user" ? "flex-row-reverse" : "flex-row",
            )}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1",
                msg.role === "user"
                  ? "bg-muted"
                  : "bg-primary/20 border border-primary/30",
              )}
            >
              {msg.role === "user" ? (
                <User className="w-4 h-4" />
              ) : (
                <Shield className="w-4 h-4 text-primary" fill="currentColor" />
              )}
            </div>
            <Card
              className={cn(
                "p-4 border-none shadow-lg max-w-[80%] rounded-[20px]",
                msg.role === "user"
                  ? "bg-muted text-foreground rounded-tr-none"
                  : "bg-card/50 text-foreground rounded-tl-none border-l-2 border-primary/50",
              )}
            >
              <p className="text-sm leading-relaxed">{msg.content}</p>
              <span className="text-[9px] opacity-40 font-bold uppercase mt-2 block">
                {msg.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </Card>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center shrink-0">
              <Shield
                className="w-4 h-4 text-primary animate-pulse"
                fill="currentColor"
              />
            </div>
            <Card className="p-4 bg-card/50 border-none rounded-[20px] rounded-tl-none flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-primary animate-spin" />
              <span className="text-xs font-bold text-primary animate-pulse">
                Analyzing...
              </span>
            </Card>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="absolute bottom-24 left-0 right-0 p-4 bg-gradient-to-t from-background via-background to-transparent pt-10">
        <form onSubmit={handleSend} className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your purchase..."
            disabled={isLoading}
            className="w-full bg-card/80 border border-white/5 rounded-full py-4 pl-6 pr-14 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 placeholder:text-muted-foreground transition-all backdrop-blur-md"
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            size="icon"
            className={cn(
              "absolute right-2 w-10 h-10 rounded-full transition-all",
              input.trim() && !isLoading
                ? "bg-primary text-background shadow-primary-glow"
                : "bg-muted text-muted-foreground opacity-50",
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </form>
        <p className="text-[10px] text-center mt-3 text-muted-foreground font-medium opacity-60">
          Encrypted & Private Financial Analysis
        </p>
      </div>
      <Navbar />
    </div>
  );
}
