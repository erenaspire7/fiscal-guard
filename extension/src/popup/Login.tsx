import { useState, useEffect, FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
// import {
//   Card,
//   CardContent,
//   CardDescription,
//   CardHeader,
//   CardTitle,
// } from "@/components/ui/card";
// import { authenticateWithGoogle } from "../background/auth";
import { StorageManager } from "../shared/storage";
import { ApiClient } from "../shared/api-client";
import {
  Shield,
  Loader2,
  Lock,
  Eye,
  EyeOff,
  Hammer,
  LogOut,
} from "lucide-react";

const storage = new StorageManager();
const apiClient = new ApiClient(storage);

export function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState<any>(null);
  // Login form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    const authenticated = await storage.isAuthenticated();
    setIsAuthenticated(authenticated);

    if (authenticated) {
      const user = await storage.getUserInfo();
      setUserInfo(user);
    }
  }

  async function handleEmailLogin(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.login(email, password);
      await storage.setAuthToken(response.access_token);

      // Fetch user info to store it
      const user = await apiClient.getCurrentUser();
      await storage.setUserInfo(user);

      await checkAuth();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  // Keeping Google login for reference/later fix
  /*
  async function handleGoogleLogin() {
    setLoading(true);
    setError(null);

    try {
      await authenticateWithGoogle();
      await checkAuth();

      // Close popup after successful login
      setTimeout(() => {
        window.close();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }
  */

  async function handleLogout() {
    await storage.clearAll();
    setIsAuthenticated(false);
    setUserInfo(null);
    setEmail("");
    setPassword("");
  }

  if (isAuthenticated && userInfo) {
    return (
      <div className="h-full w-full bg-background p-6 flex flex-col items-center">
        <div className="w-full max-w-sm flex-1 flex flex-col items-center pt-8">
          <div className="flex flex-col items-center gap-4 mb-8">
            <div className="p-3 rounded-full bg-primary/10">
              <Shield className="size-8 text-primary" />
            </div>
            <div className="flex flex-col items-center gap-3">
              <h2 className="text-xl font-semibold tracking-tight">
                Fiscal Guard
              </h2>
              <div className="flex items-center gap-2 bg-secondary/50 px-3 py-1.5 rounded-full border border-border">
                <div className="size-5 rounded-full bg-primary/20 flex items-center justify-center">
                  <span className="text-[10px] font-medium text-primary">
                    {userInfo.email?.[0]?.toUpperCase()}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {userInfo.email}
                </span>
              </div>
            </div>
          </div>

          <div className="w-full border-2 border-dashed border-border rounded-xl p-6 flex flex-col items-center text-center gap-3 bg-card/30">
            <Hammer className="size-8 text-primary/80 mb-1" />
            <h3 className="font-medium">Under Construction</h3>
            <p className="text-xs text-muted-foreground leading-relaxed px-2">
              More features are being built. Cart analysis runs automatically in
              the background.
            </p>
          </div>
        </div>

        <div className="w-full pb-4">
          <Button
            variant="ghost"
            onClick={handleLogout}
            className="w-full text-muted-foreground hover:text-foreground gap-2"
          >
            <LogOut className="size-4" />
            Sign out
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-background p-6 flex flex-col items-center justify-center">
      <div className="w-full max-w-[320px] space-y-6">
        {/* Header / Lock Icon */}
        <div className="flex flex-col items-center space-y-4">
          <Lock className="size-10 text-primary" />
          <div className="text-center space-y-1">
            <h1 className="text-xl font-semibold tracking-tight">
              Fiscal Guard
            </h1>
            <p className="text-sm text-muted-foreground">
              Sign in to your account
            </p>
          </div>
        </div>

        {/* Login Form */}
        <form onSubmit={handleEmailLogin} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="bg-secondary/50 border-border text-sm"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-secondary/50 border-border pr-10 text-sm"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeOff className="size-4 text-muted-foreground" />
                ) : (
                  <Eye className="size-4 text-muted-foreground" />
                )}
              </Button>
            </div>
          </div>

          {error && (
            <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full h-10 font-medium"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Unlocking...
              </>
            ) : (
              "Unlock"
            )}
          </Button>
        </form>

        <div className="space-y-2 text-center">
          {/* Google Login (Commented out UI as requested) */}
          {/*
            <div className="relative">
                <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                    Or continue with
                </span>
                </div>
            </div>

            <Button variant="outline" onClick={handleGoogleLogin} disabled={loading} className="w-full">
                <svg className="mr-2 size-4" viewBox="0 0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Google
            </Button>
            */}
        </div>

        <div>
          <p className="text-xs text-muted-foreground text-center">
            Don't have an account?{" "}
            <a href="#" className="text-primary hover:underline">
              Sign up
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
