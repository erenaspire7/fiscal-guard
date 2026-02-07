import { Link } from "react-router-dom";
import { Shield } from "lucide-react";

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-[#020804] text-white font-sans overflow-x-hidden selection:bg-emerald-500/30 selection:text-white">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full relative z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
            <Shield className="w-4 h-4 fill-emerald-500/20" />
          </div>
          <span className="font-semibold text-sm text-white tracking-wide">
            Fiscal Guard
          </span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
          <a
            href="#features"
            className="hover:text-emerald-400 transition-colors"
          >
            Features
          </a>
          <a
            href="#insights"
            className="hover:text-emerald-400 transition-colors"
          >
            Insights
          </a>
          <a
            href="#security"
            className="hover:text-emerald-400 transition-colors"
          >
            Security
          </a>
        </div>

        <Link
          to="/login"
          className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2 rounded-xl font-medium text-sm transition-all shadow-lg shadow-emerald-900/20"
        >
          Sign In
        </Link>
      </nav>

      {/* Hero Section */}
      <div className="relative pt-20 pb-32 flex flex-col items-center justify-center text-center px-4">
        {/* Background Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-150 bg-emerald-500/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="mb-8 relative z-10">
          <div className="w-16 h-16 rounded-2xl border border-emerald-500/20 flex items-center justify-center bg-emerald-500/10 mx-auto shadow-[0_0_30px_rgba(16,185,129,0.1)]">
            <Shield className="w-8 h-8 text-emerald-500 fill-emerald-500/20" />
          </div>
        </div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 relative z-10 leading-[1.1]">
          Prevent Buyer's
          <br />
          <span className="text-emerald-500">Remorse</span>
        </h1>

        <p className="text-gray-400 max-w-xl mx-auto text-lg mb-10 leading-relaxed relative z-10">
          Fiscal Guard is an AI-powered financial assistant that analyzes your
          budget, goals, and spending patterns before you buy. Intervening at
          the moment of decision.
        </p>

        <Link
          to="/register"
          className="relative z-10 bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-4 rounded-xl font-medium text-sm transition-all shadow-lg shadow-emerald-900/20 hover:scale-105"
        >
          Activate Guard
        </Link>
      </div>

      {/* Stats Section */}
      <div className="max-w-4xl mx-auto px-4 mb-40 relative z-10">
        <div className="bg-[#040d07] border border-white/5 rounded-3xl p-12 pb-16 text-center relative overflow-hidden group shadow-2xl">
          <div className="absolute inset-0 bg-linear-to-b from-transparent to-black/50 pointer-events-none" />

          <h3 className="text-emerald-500 text-xs font-semibold uppercase tracking-wider mb-8">
            The Impulse Problem
          </h3>

          <div className="mb-12">
            <span className="text-6xl md:text-8xl font-bold tracking-tight text-white block mb-4">
              $3,381
            </span>
            <p className="text-gray-500 text-sm">
              Average annual spend on impulse purchases in the U.S.
            </p>
          </div>

          <div className="flex flex-col md:flex-row justify-center gap-16 md:gap-32 px-4">
            <div className="flex flex-col items-center">
              <span className="text-4xl font-bold text-white mb-2">64%</span>
              <p className="text-gray-500 text-xs max-w-[150px]">
                Of people regret their impulse decisions.
              </p>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-4xl font-bold text-white mb-2">32%</span>
              <p className="text-gray-500 text-xs max-w-[150px]">
                Have delayed a major milestone due to impulse buying.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 pb-40 relative z-10" id="features">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 tracking-tight">
            Active <span className="text-emerald-500">Intervention</span>
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-sm leading-relaxed">
            Powered by a Multi-Agent System (Strands + Gemini 2.5) and Real-Time
            Observability (Opik).
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="group bg-[#040d07] rounded-3xl border border-white/5 hover:border-emerald-500/20 transition-all duration-300 overflow-hidden shadow-lg hover:shadow-emerald-900/10">
            <div className="h-48 overflow-hidden relative">
              <div className="absolute inset-0 bg-emerald-900/20 mix-blend-overlay z-10" />
              <a
                href="https://unsplash.com"
                target="_blank"
                rel="noopener noreferrer"
                className="absolute bottom-3 right-3 z-20 text-[10px] text-white/60 hover:text-white bg-black/40 hover:bg-black/60 px-2 py-1 rounded-lg backdrop-blur-sm transition-all opacity-0 group-hover:opacity-100"
              >
                Unsplash
              </a>
              <img
                src="https://images.unsplash.com/photo-1755282464684-6568f7f76b5d?q=80&w=2370&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
                alt="AI Chat"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 opacity-80 group-hover:opacity-100 grayscale group-hover:grayscale-0"
              />
            </div>
            <div className="p-8">
              <h3 className="font-semibold text-sm mb-3 text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" />
                SHIELD (AGENT CHAT)
              </h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Direct chat for real-time purchase analysis. Checks Budget,
                Goals, and Regret Patterns before you spend.
              </p>
            </div>
          </div>

          {/* Card 2 */}
          <div className="group bg-[#040d07] rounded-3xl border border-white/5 hover:border-emerald-500/20 transition-all duration-300 overflow-hidden shadow-lg hover:shadow-emerald-900/10">
            <div className="h-48 overflow-hidden relative">
              <div className="absolute inset-0 bg-emerald-900/20 mix-blend-overlay z-10" />
              <a
                href="https://unsplash.com"
                target="_blank"
                rel="noopener noreferrer"
                className="absolute bottom-3 right-3 z-20 text-[10px] text-white/60 hover:text-white bg-black/40 hover:bg-black/60 px-2 py-1 rounded-lg backdrop-blur-sm transition-all opacity-0 group-hover:opacity-100"
              >
                Unsplash
              </a>
              <img
                src="https://images.unsplash.com/photo-1496096265110-f83ad7f96608?q=80&w=2370&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
                alt="Dashboard"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 opacity-80 group-hover:opacity-100 grayscale group-hover:grayscale-0"
              />
            </div>
            <div className="p-8">
              <h3 className="font-semibold text-sm mb-3 text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" />
                COMMAND & INSIGHTS
              </h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Track your Guard Score (0-100) and identify regret triggers.
                Close the loop on past decisions.
              </p>
            </div>
          </div>

          {/* Card 3 */}
          <div className="group bg-[#040d07] rounded-3xl border border-white/5 hover:border-emerald-500/20 transition-all duration-300 overflow-hidden shadow-lg hover:shadow-emerald-900/10">
            <div className="h-48 overflow-hidden relative">
              <div className="absolute inset-0 bg-emerald-900/20 mix-blend-overlay z-10" />
              <a
                href="https://unsplash.com"
                target="_blank"
                rel="noopener noreferrer"
                className="absolute bottom-3 right-3 z-20 text-[10px] text-white/60 hover:text-white bg-black/40 hover:bg-black/60 px-2 py-1 rounded-lg backdrop-blur-sm transition-all opacity-0 group-hover:opacity-100"
              >
                Unsplash
              </a>
              <img
                src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=800"
                alt="Budgets"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 opacity-80 group-hover:opacity-100 grayscale group-hover:grayscale-0"
              />
            </div>
            <div className="p-8">
              <h3 className="font-semibold text-sm mb-3 text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" />
                VAULT
              </h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Manage smart budgets and goals. Secure your assets and
                contribute to long-term wealth.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="py-32 relative overflow-hidden bg-[#040d07]">
        {/* Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-150 h-100 bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative z-10 text-center px-4">
          <h2 className="text-3xl md:text-4xl font-bold mb-6 tracking-tight">
            Ready to master{" "}
            <span className="text-emerald-500">your spending?</span>
          </h2>
          <p className="text-gray-400 mb-12 max-w-md mx-auto text-sm">
            Join users who are making smarter financial decisions with Fiscal
            Guard's AI intervention.
          </p>
          <Link
            to="/register"
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-4 rounded-xl font-medium text-sm transition-all shadow-lg shadow-emerald-900/20 hover:scale-105"
          >
            Activate Guard
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-[#020804] text-sm text-gray-500">
        <div className="max-w-7xl mx-auto px-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="font-medium">
            Fiscal Guard © {new Date().getFullYear()}
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
