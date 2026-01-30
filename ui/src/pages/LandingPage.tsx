import { Link } from "react-router-dom";
import { Shield, Activity } from "lucide-react";

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-[#021206] text-white font-sans overflow-x-hidden selection:bg-green-500 selection:text-black">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full relative z-10">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-green-500" />
          <span className="font-bold tracking-widest text-sm text-white">
            FISCAL GUARD
          </span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-[11px] font-semibold text-gray-400 tracking-wider uppercase">
          <a
            href="#features"
            className="hover:text-green-400 transition-colors"
          >
            Features
          </a>
          <a
            href="#insights"
            className="hover:text-green-400 transition-colors"
          >
            Insights
          </a>
          <a
            href="#security"
            className="hover:text-green-400 transition-colors"
          >
            Security
          </a>
        </div>

        <Link
          to="/login"
          className="bg-green-500 hover:bg-green-400 text-black px-6 py-2 rounded-sm font-bold text-[11px] tracking-wider transition-all transform hover:scale-105"
        >
          LOGIN
        </Link>
      </nav>

      {/* Hero Section */}
      <div className="relative pt-20 pb-32 flex flex-col items-center justify-center text-center px-4">
        {/* Background Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-150 bg-green-900/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="mb-10 relative z-10">
          <div className="w-20 h-20 rounded-full border border-green-500/20 flex items-center justify-center bg-green-500/5 mx-auto shadow-[0_0_30px_rgba(34,197,94,0.1)]">
            <Shield className="w-9 h-9 text-green-500" />
          </div>
        </div>

        <h1 className="text-5xl md:text-7xl font-black tracking-tighter mb-6 relative z-10 leading-[0.9]">
          PREVENT BUYER'S
          <br />
          <span className="text-green-500">REMORSE</span>
        </h1>

        <p className="text-gray-400 max-w-xl mx-auto text-base mb-12 leading-relaxed relative z-10 font-medium">
          Your AI Financial Companion. Fiscal Guard intervenes at the moment of
          decision to analyze your budget, goals, and spending patterns{" "}
          <strong>before</strong> you buy.
        </p>

        <Link
          to="/register"
          className="relative z-10 bg-green-500 hover:bg-green-400 text-black px-8 py-4 rounded-sm font-bold text-xs tracking-[0.15em] uppercase transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(34,197,94,0.3)]"
        >
          Activate Guard
        </Link>
      </div>

      {/* Stats Section */}
      <div className="max-w-4xl mx-auto px-4 mb-40 relative z-10">
        <div className="bg-[#031c0a] border border-green-500/10 rounded-sm p-12 text-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-linear-to-b from-transparent to-black/50 pointer-events-none" />

          <h3 className="text-green-500 text-[10px] font-bold tracking-[0.2em] uppercase mb-4 opacity-80">
            The Impulse Problem
          </h3>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4 mb-2">
            <span className="text-5xl md:text-7xl font-bold tracking-tight text-white group-hover:text-green-50 transition-colors">
              $21,000
            </span>
            <div className="flex items-center gap-1.5 text-green-500 md:self-start md:mt-2">
              <Activity className="w-3 h-3" />
              <span className="text-[10px] font-bold uppercase tracking-wider">
                Avg
              </span>
            </div>
          </div>

          <p className="text-gray-500 italic text-xs mt-4">
            Average amount Americans spend yearly on purchases they later
            regret.
          </p>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 pb-40 relative z-10" id="features">
        <h2 className="text-3xl md:text-4xl font-bold mb-4 tracking-tighter">
          ACTIVE <span className="text-green-500">INTERVENTION</span>
        </h2>
        <p className="text-gray-400 mb-16 max-w-xl text-sm leading-relaxed">
          Powered by Strands + Gemini 2.5 and Opik observability to guide your
          financial decisions.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="group bg-[#051108] rounded border border-white/5 hover:border-green-500/30 transition-all duration-300">
            <div className="h-40 overflow-hidden relative">
              <div className="absolute inset-0 bg-green-900/20 mix-blend-overlay z-10" />
              <img
                src="https://images.unsplash.com/photo-1639322537228-f710d846310a?auto=format&fit=crop&q=80&w=800"
                alt="AI Chat"
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 opacity-60 group-hover:opacity-80 grayscale group-hover:grayscale-0"
              />
            </div>
            <div className="p-8">
              <h3 className="font-bold text-xs mb-3 uppercase tracking-widest text-white">
                Shield (Agent Chat)
              </h3>
              <p className="text-gray-400 text-[13px] leading-relaxed">
                Direct chat for real-time purchase analysis. Checks Budget,
                Goals, and Regret Patterns before you spend.
              </p>
            </div>
          </div>

          {/* Card 2 */}
          <div className="group bg-[#051108] rounded border border-white/5 hover:border-green-500/30 transition-all duration-300">
            <div className="h-40 overflow-hidden relative">
              <div className="absolute inset-0 bg-green-900/20 mix-blend-overlay z-10" />
              <img
                src="https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&q=80&w=800"
                alt="Dashboard"
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 opacity-60 group-hover:opacity-80 grayscale group-hover:grayscale-0"
              />
            </div>
            <div className="p-8">
              <h3 className="font-bold text-xs mb-3 uppercase tracking-widest text-white">
                Command & Insights
              </h3>
              <p className="text-gray-400 text-[13px] leading-relaxed">
                Track your Guard Score (0-100) and identify regret triggers.
                Close the loop on past decisions.
              </p>
            </div>
          </div>

          {/* Card 3 */}
          <div className="group bg-[#051108] rounded border border-white/5 hover:border-green-500/30 transition-all duration-300">
            <div className="h-40 overflow-hidden relative">
              <div className="absolute inset-0 bg-green-900/20 mix-blend-overlay z-10" />
              <img
                src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=800"
                alt="Budgets"
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 opacity-60 group-hover:opacity-80 grayscale group-hover:grayscale-0"
              />
            </div>
            <div className="p-8">
              <h3 className="font-bold text-xs mb-3 uppercase tracking-widest text-white">
                Vault
              </h3>
              <p className="text-gray-400 text-[13px] leading-relaxed">
                Manage smart budgets and goals. Secure your assets and
                contribute to long-term wealth.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="py-32 relative overflow-hidden bg-[#031106]">
        {/* Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-150 h-100 bg-green-500/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative z-10 text-center px-4">
          <h2 className="text-3xl md:text-4xl font-bold mb-6 tracking-tighter">
            READY TO MASTER{" "}
            <span className="text-green-500">YOUR SPENDING?</span>
          </h2>
          <p className="text-gray-400 mb-12 max-w-md mx-auto text-sm">
            Join users who are making smarter financial decisions with Fiscal
            Guard's AI intervention.
          </p>
          <Link
            to="/register"
            className="bg-green-500 hover:bg-green-400 text-black px-10 py-4 rounded-sm font-bold text-xs tracking-[0.15em] uppercase transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(34,197,94,0.3)]"
          >
            Activate Guard
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-[#020d04] text-[10px] font-bold text-gray-600 tracking-widest uppercase">
        <div className="max-w-7xl mx-auto px-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div>Fiscal Guard © {new Date().getFullYear()}</div>
          <div className="flex gap-8">
            <a href="#" className="hover:text-green-500 transition-colors">
              Privacy Protocol
            </a>
            <a href="#" className="hover:text-green-500 transition-colors">
              Terminal Terms
            </a>
            <a href="#" className="hover:text-green-500 transition-colors">
              API Access
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
