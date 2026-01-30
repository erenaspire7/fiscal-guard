/**
 * Extension constants
 */

// API Configuration
export const API_URL =
  (import.meta.env && import.meta.env.VITE_API_URL) || "http://localhost:8000";

// Google OAuth Configuration
export const GOOGLE_CLIENT_ID =
  (import.meta.env && import.meta.env.VITE_GOOGLE_CLIENT_ID) || "";

// Extension Configuration
export const EXTENSION_NAME = "Fiscal Guard";
export const EXTENSION_VERSION = "0.1.0";

// Message Types for Chrome messaging
export const MESSAGE_TYPES = {
  ANALYZE_CART: "analyze-cart",
  CAPTURE_SCREENSHOT: "capture-screenshot",
  GET_AUTH_TOKEN: "get-auth-token",
  LOGOUT: "logout",
} as const;

// Page Types
export const PAGE_TYPES = {
  CART: "cart",
  CHECKOUT: "checkout",
  PRODUCT: "product",
} as const;

// Decision Score Categories
export const DECISION_CATEGORIES = {
  STRONG_NO: "strong_no",
  MILD_NO: "mild_no",
  NEUTRAL: "neutral",
  MILD_YES: "mild_yes",
  STRONG_YES: "strong_yes",
} as const;
