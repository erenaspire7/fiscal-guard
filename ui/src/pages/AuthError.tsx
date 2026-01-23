import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';

export default function AuthError() {
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState('Authentication failed');

  useEffect(() => {
    // Extract error message from URL query parameters
    const params = new URLSearchParams(window.location.search);
    const message = params.get('message');

    if (message) {
      setErrorMessage(message);
    }
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full mx-4">
        <div className="bg-card border border-destructive/50 rounded-lg p-6 shadow-lg">
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="h-6 w-6 text-destructive" />
            <h1 className="text-xl font-semibold text-foreground">Authentication Error</h1>
          </div>

          <p className="text-muted-foreground mb-6">{errorMessage}</p>

          <button
            onClick={() => navigate('/login', { replace: true })}
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-medium py-2 px-4 rounded-md transition-colors"
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}
