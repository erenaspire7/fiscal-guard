import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Shield, Mail, Lock, Loader2, Chrome } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { env } from "@/config/env";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleLogin = () => {
    window.location.href = `${env.apiUrl}/auth/google/login`;
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${env.apiUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Login failed. Please check your credentials.",
        );
      }

      login(data.access_token);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred",
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020804] text-white font-sans flex items-center justify-center p-4 selection:bg-emerald-500/30">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link
            to="/"
            className="inline-flex items-center gap-2 justify-center mb-6 transition-transform hover:scale-105"
          >
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-500">
              <Shield className="w-6 h-6 fill-emerald-500/20" />
            </div>
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome back
          </h1>
          <p className="text-gray-400 text-sm mt-2">
            Enter your credentials to access your account
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-[#040d07] border border-white/5 rounded-2xl p-8 shadow-2xl">
          <form onSubmit={handlePasswordLogin} className="space-y-6">
            <div className="space-y-3">
              <div>
                <label
                  htmlFor="email"
                  className="text-sm font-medium text-gray-300 ml-1"
                >
                  Email
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Mail className="h-4 w-4 text-gray-500" />
                </div>
                <input
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full bg-[#010402] border border-white/5 text-white text-sm rounded-xl focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 block w-full pl-10 p-3 placeholder-gray-500 transition-all outline-none shadow-inner"
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between ml-1">
                <label
                  htmlFor="password"
                  className="text-sm font-medium text-gray-300"
                >
                  Password
                </label>
                <a
                  href="#"
                  className="text-xs text-emerald-500 hover:text-emerald-400 transition-colors"
                >
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-gray-500" />
                </div>
                <input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-[#010402] border border-white/5 text-white text-sm rounded-xl focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 block w-full pl-10 p-3 placeholder-gray-500 transition-all outline-none shadow-inner"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/10 text-red-400 text-xs text-center">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-3 px-4 rounded-xl transition-all shadow-lg shadow-emerald-900/20 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/5" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-[#040d07] px-3 text-gray-500">
                Or continue with
              </span>
            </div>
          </div>

          <button
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className="w-full bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium py-3 px-4 rounded-xl transition-all flex items-center justify-center gap-2.5 text-sm"
          >
            <Chrome className="w-4 h-4" />
            Google
          </button>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          Don't have an account?{" "}
          <Link
            to="/register"
            className="text-emerald-500 hover:text-emerald-400 font-medium hover:underline transition-colors"
          >
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
