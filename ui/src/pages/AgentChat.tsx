import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import { useChat } from "@/hooks/useChat";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Send, Shield, User, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeBackgrounds, DEFAULT_THEME } from "@/lib/themes";
import { useAuth } from "@/contexts/AuthContext";

export default function AgentChat() {
  const navigate = useNavigate();
  const { messages, sendMessage, isLoading } = useChat();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();

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
    <div
      className={cn(
        "flex h-screen text-foreground font-sans overflow-hidden transition-all duration-300",
        ThemeBackgrounds[DEFAULT_THEME],
      )}
    >
      <Sidebar />
      <div className="flex-1 flex flex-col h-full relative md:pl-64 w-full transition-all duration-300">
        {/* Sticky Header */}
        <header className="p-4 md:p-6 z-10 shrink-0 w-full flex justify-center">
          <div className="flex flex-col items-center justify-center gap-2">
            <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center border border-primary/20">
              <Shield className="w-6 h-6 text-primary" />
            </div>
            <div className="text-center">
              <h1 className="font-bold text-lg">Fiscal Guard Agent</h1>
              <div className="flex items-center justify-center gap-2 mt-1">
                <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                <p className="text-[10px] uppercase tracking-widest text-primary font-bold opacity-80">
                  Active Session
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Content Container */}
        <div className="flex-1 flex flex-col w-full max-w-5xl mx-auto relative overflow-hidden">
          {/* Chat Area */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-5 md:p-8 space-y-6 scroll-smooth pb-32 md:pb-32"
          >
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-60">
                <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-2">
                  <Shield className="w-8 h-8 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium px-12 md:text-base md:max-w-md">
                  Welcome back. Tell me about a purchase you're considering, and
                  I'll help you decide if it aligns with your goals.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-8 w-full max-w-2xl px-4">
                  {[
                    "I want to buy a new gaming headset for $150",
                    "Is a $45 dinner out okay today?",
                    "Analyze my subscription costs",
                  ].map((text, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setInput(text);
                      }}
                      className={cn(
                        "text-xs md:text-sm p-3 md:p-4 rounded-2xl border border-white/5 bg-white/5 hover:bg-primary/10 hover:border-primary/20 hover:text-primary transition-all text-center",
                        i === 2 && "md:col-span-2",
                      )}
                    >
                      "{text}"
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex w-full gap-4",
                  msg.role === "user" ? "flex-row-reverse" : "flex-row",
                )}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1",
                    msg.role === "user"
                      ? "bg-white"
                      : "border border-primary/30",
                  )}
                >
                  {msg.role === "user" ? (
                    <img
                      src={
                        user?.picture ||
                        `https://api.dicebear.com/7.x/notionists-neutral/svg?seed=${
                          user?.name || user?.email?.split("@")[0] || "user"
                        }`
                      }
                      alt="User"
                      className="w-full h-full rounded-full"
                    />
                  ) : (
                    <Shield className="w-4 h-4 text-primary" />
                  )}
                </div>

                <div className="flex flex-col max-w-[80%]">
                  <Card
                    className={cn(
                      "p-4 border-none shadow-none rounded-2xl",
                      msg.role === "user"
                        ? "bg-primary/20 text-foreground"
                        : "bg-[#0A2A22] text-foreground/90",
                    )}
                  >
                    <div className="text-sm leading-relaxed font-sans">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => (
                            <p className="mb-3 last:mb-0">{children}</p>
                          ),
                          ul: ({ children }) => (
                            <ul className="list-disc pl-4 mb-3 last:mb-0 space-y-1">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal pl-4 mb-3 last:mb-0 space-y-1">
                              {children}
                            </ol>
                          ),
                          li: ({ children }) => (
                            <li className="mb-1">{children}</li>
                          ),
                          strong: ({ children }) => (
                            <strong className="font-semibold text-primary">
                              {children}
                            </strong>
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </Card>
                  <span
                    className={cn(
                      "text-[10px] text-muted-foreground/60 mt-2 font-medium",
                      msg.role === "user" ? "text-right" : "text-left",
                    )}
                  >
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex w-full gap-4 flex-row">
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 border border-primary/30">
                  <Shield className="w-4 h-4 text-primary" />
                </div>
                <div className="flex flex-col max-w-[30%] w-full">
                  <Card className="p-5 border-none shadow-none rounded-2xl bg-[#0A2A22] text-foreground/90">
                    <div className="space-y-2.5">
                      <Skeleton className="h-2 w-[75%] bg-primary/10" />
                      <Skeleton className="h-2 w-[90%] bg-primary/10" />
                      <Skeleton className="h-2 w-[60%] bg-primary/10" />
                    </div>
                  </Card>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="absolute bottom-24 md:bottom-0 left-0 right-0 p-4 md:p-8 z-20 pt-12">
            <div className="max-w-3xl mx-auto">
              <form
                onSubmit={handleSend}
                className="relative flex items-center"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Describe your purchase..."
                  disabled={isLoading}
                  className="w-full bg-[#0A2A22]/50 border border-white/10 rounded-2xl py-5 pl-6 pr-16 text-sm focus:outline-none focus:ring-1 focus:ring-primary/50 placeholder:text-muted-foreground/50 transition-all backdrop-blur-xl shadow-2xl text-white"
                />
                <Button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  size="icon"
                  className={cn(
                    "absolute right-3 w-10 h-10 rounded-xl transition-all",
                    input.trim() && !isLoading
                      ? "bg-primary text-background hover:bg-primary/90"
                      : "bg-white/10 text-white/20",
                  )}
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </Button>
              </form>
            </div>
          </div>
          <div className="md:hidden">
            <Navbar />
          </div>
        </div>
      </div>
    </div>
  );
}
