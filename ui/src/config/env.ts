/**
 * Centralized environment configuration
 * All environment variables should be accessed through this file
 */

export const env = {
  apiUrl: import.meta.env.VITE_API_URL,
} as const;
