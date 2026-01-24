import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Chrome, Mail, Lock, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group";
import { Label } from "@/components/ui/label";
import { Field, FieldLabel, FieldError } from "@/components/ui/field";
import { useAuth } from "@/contexts/AuthContext";
import { env } from "@/config/env";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleLogin = () => {
    // Redirect to backend Google OAuth endpoint
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
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
              <span className="text-2xl">💰</span>
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">Fiscal Guard</CardTitle>
          <CardDescription>
            Sign in to protect your financial future
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handlePasswordLogin} className="space-y-4">
            <Field>
              <FieldLabel>
                <Label htmlFor="email">Email</Label>
              </FieldLabel>
              <InputGroup>
                <InputGroupAddon>
                  <Mail className="h-4 w-4" />
                </InputGroupAddon>
                <InputGroupInput
                  id="email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </InputGroup>
            </Field>

            <Field>
              <FieldLabel>
                <Label htmlFor="password">Password</Label>
              </FieldLabel>
              <InputGroup>
                <InputGroupAddon>
                  <Lock className="h-4 w-4" />
                </InputGroupAddon>
                <InputGroupInput
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </InputGroup>
            </Field>

            {error && <FieldError className="text-center">{error}</FieldError>}

            <Button type="submit" className="w-full h-11" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </Button>
          </form>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">
                Or continue with
              </span>
            </div>
          </div>

          <Button
            onClick={handleGoogleLogin}
            variant="outline"
            className="w-full h-11 gap-2"
            disabled={isLoading}
          >
            <Chrome className="w-5 h-5" />
            Sign in with Google
          </Button>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4 text-center text-sm text-muted-foreground">
          <div>
            Don't have an account?{" "}
            <Link
              to="/register"
              className="text-primary hover:underline font-medium"
            >
              Sign up
            </Link>
          </div>
          <div className="text-xs opacity-70">
            By signing in, you agree to make smarter financial decisions
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
