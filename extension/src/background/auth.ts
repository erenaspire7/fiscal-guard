/**
 * OAuth authentication handler for Chrome extension
 */

import { GOOGLE_CLIENT_ID } from "../shared/constants";
import { ApiClient } from "../shared/api-client";
import { StorageManager } from "../shared/storage";

const storage = new StorageManager();
const apiClient = new ApiClient(storage);

/**
 * Generate random nonce for OAuth
 */
function generateNonce(): string {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
}

/**
 * Extract ID token from OAuth redirect URL
 */
function extractIdToken(url: string): string | null {
  const match = url.match(/[#&]id_token=([^&]+)/);
  return match ? match[1] : null;
}

/**
 * Authenticate with Google OAuth popup
 */
export async function authenticateWithGoogle(): Promise<string> {
  try {
    // Try to use existing Chrome Google account (fast path)
    // This uses chrome.identity.getAuthToken which is simpler
    try {
      const result = await chrome.identity.getAuthToken({ interactive: true });

      if (result?.token) {
        // Exchange with backend
        const authResponse = await apiClient.exchangeGoogleToken(result.token);

        // Store token and user info
        await storage.setAuthToken(authResponse.access_token);
        await storage.setUserInfo(authResponse.user);

        return authResponse.access_token;
      }
    } catch (error) {
      console.log("getAuthToken failed, using webAuthFlow fallback", error);
    }

    // Fallback: Launch OAuth popup (more manual flow)
    const redirectURL = chrome.identity.getRedirectURL();
    const scopes = ["openid", "email", "profile"];
    const nonce = generateNonce();

    const authUrl =
      `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=${GOOGLE_CLIENT_ID}&` +
      `response_type=token id_token&` +
      `redirect_uri=${encodeURIComponent(redirectURL)}&` +
      `scope=${encodeURIComponent(scopes.join(" "))}&` +
      `nonce=${nonce}`;

    const responseUrl = await chrome.identity.launchWebAuthFlow({
      url: authUrl,
      interactive: true,
    });

    // Extract ID token from response URL
    if (!responseUrl) {
      throw new Error("OAuth flow did not return a response URL");
    }

    const idToken = extractIdToken(responseUrl);
    if (!idToken) {
      throw new Error("Failed to extract ID token from OAuth response");
    }

    // Exchange with backend
    const authResponse = await apiClient.exchangeGoogleToken(idToken);

    // Store token and user info
    await storage.setAuthToken(authResponse.access_token);
    await storage.setUserInfo(authResponse.user);

    return authResponse.access_token;
  } catch (error) {
    console.error("Authentication failed:", error);
    throw error;
  }
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  await storage.clearAuthToken();
  await storage.clearAll();
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  return await storage.isAuthenticated();
}
