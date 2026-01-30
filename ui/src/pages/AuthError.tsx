import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle } from "lucide-react";

export default function AuthError() {
  const navigate = useNavigate();

  // Initialize state directly from URL params to avoid useEffect and re-renders
  const [errorMessage] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("message") || "Authentication failed";
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full mx-4">
        <div className="bg-card border border-destructive/50 rounded-lg p-6 shadow-lg">
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="h-6 w-6 text-destructive" />
            <h1 className="text-xl font-semibold text-foreground">
              Authentication Error
            </h1>
          </div>

          <p className="text-muted-foreground mb-6">{errorMessage}</p>

          <button
            onClick={() => navigate("/login", { replace: true })}
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-medium py-2 px-4 rounded-md transition-colors"
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}
