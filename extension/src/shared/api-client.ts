/**
 * API client for communicating with Fiscal Guard backend
 */

import { API_URL } from "./constants";
import { StorageManager } from "./storage";
import type {
  CartAnalysisRequest,
  CartAnalysisResponse,
  ChatResponse,
  AuthResponse,
  VisionExtractionResult,
} from "./types";

export class ApiClient {
  private storage: StorageManager;

  constructor(storage: StorageManager) {
    this.storage = storage;
  }

  /**
   * Exchange Google ID token for Fiscal Guard JWT
   */
  async exchangeGoogleToken(idToken: string): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/auth/google/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ id_token: idToken }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Token exchange failed");
    }

    return await response.json();
  }

  /**
   * Login with email and password
   */
  async login(
    email: string,
    password: string,
  ): Promise<{ access_token: string }> {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    return await response.json();
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<any> {
    const token = await this.storage.getAuthToken();
    if (!token) {
      throw new Error("Not authenticated");
    }

    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        await this.storage.clearAuthToken();
        throw new Error("Authentication expired. Please login again.");
      }
      throw new Error("Failed to get user info");
    }

    return await response.json();
  }

  /**
   * Extract cart items from screenshot using backend Vision Agent
   */
  async extractCartFromScreenshot(
    screenshotBlob: Blob,
    pageUrl: string,
    pageType: string = "cart",
  ): Promise<VisionExtractionResult> {
    const token = await this.storage.getAuthToken();
    if (!token) {
      throw new Error("Not authenticated");
    }

    // Convert blob to base64
    const base64 = await this.blobToBase64(screenshotBlob);

    const response = await fetch(
      `${API_URL}/decisions/extract-cart-screenshot`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          image_base64: base64,
          page_url: pageUrl,
          page_type: pageType,
        }),
      },
    );

    if (!response.ok) {
      if (response.status === 401) {
        await this.storage.clearAuthToken();
        throw new Error("Authentication expired. Please login again.");
      }
      const error = await response.json();
      throw new Error(error.detail || "Screenshot extraction failed");
    }

    const data = await response.json();

    return {
      items: data.items,
      success: true,
      extractionQuality: data.extraction_quality,
      confidenceScore: data.confidence_score,
      warnings: data.warnings,
      validationReport: data.validation_report,
    };
  }

  /**
   * Analyze cart items
   */
  async analyzeCart(
    request: CartAnalysisRequest,
  ): Promise<CartAnalysisResponse> {
    const token = await this.storage.getAuthToken();
    if (!token) {
      throw new Error("Not authenticated");
    }

    const response = await fetch(`${API_URL}/decisions/analyze-cart`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Clear invalid token
        await this.storage.clearAuthToken();
        throw new Error("Authentication expired. Please login again.");
      }
      const error = await response.json();
      throw new Error(error.detail || "Cart analysis failed");
    }

    return await response.json();
  }

  /**
   * Convert blob to base64 string
   */
  private async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        resolve(reader.result as string);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Send chat message for follow-up questions
   */
  async sendChatMessage(
    message: string,
    conversationId: string,
    conversationHistory: any[] = [],
  ): Promise<ChatResponse> {
    const token = await this.storage.getAuthToken();
    if (!token) {
      throw new Error("Not authenticated");
    }

    const response = await fetch(`${API_URL}/chat/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        conversation_history: conversationHistory,
      }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        await this.storage.clearAuthToken();
        throw new Error("Authentication expired. Please login again.");
      }
      const error = await response.json();
      throw new Error(error.detail || "Chat request failed");
    }

    return await response.json();
  }

  /**
   * Verify current token is valid
   */
  async verifyToken(): Promise<boolean> {
    const token = await this.storage.getAuthToken();
    if (!token) {
      return false;
    }

    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        await this.storage.clearAuthToken();
        return false;
      }

      return true;
    } catch {
      return false;
    }
  }
}
