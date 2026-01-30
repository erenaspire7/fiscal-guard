/**
 * Main content script - orchestrates cart analysis flow
 */

// Polyfill process to prevent ReferenceError from dependencies expecting Node.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
if (typeof (globalThis as any).process === "undefined") {
  (globalThis as any).process = {
    env: { NODE_ENV: "production" },
    nextTick: (fn: () => void) => setTimeout(fn, 0),
  };
}

import { AmazonDetector } from "./AmazonDetector";
import { ScreenshotCapture } from "./ScreenshotCapture";
import { injectFloatingSidebar } from "./ShadowDOM";
import { ApiClient } from "../shared/api-client";
import { StorageManager } from "../shared/storage";

class FiscalGuardExtension {
  private apiClient: ApiClient;
  private storage: StorageManager;
  private activeSidebar: (() => void) | null = null;
  private isProcessing = false;

  constructor() {
    this.storage = new StorageManager();
    this.apiClient = new ApiClient(this.storage);
  }

  /**
   * Initialize extension
   */
  async initialize() {
    console.log("[Fiscal Guard] Extension initialized");

    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
      if (message.action === "analyze-cart") {
        this.handleAnalyzeCart()
          .then(() => sendResponse({ success: true }))
          .catch((error) =>
            sendResponse({ success: false, error: error.message }),
          );
        return true; // Keep channel open for async response
      }
    });

    // Check page context periodically to show nudges
    this.checkPageContext();
    setInterval(() => this.checkPageContext(), 2000);
  }

  /**
   * Check if we should show a nudge (Login or Analyze)
   */
  async checkPageContext() {
    // Don't show nudges if sidebar is active or processing
    if (this.activeSidebar || this.isProcessing) {
      this.removeNudges();
      return;
    }

    const detector = new AmazonDetector();
    const pageInfo = detector.detect();

    if (
      pageInfo.isAmazon &&
      (pageInfo.pageType === "cart" || pageInfo.pageType === "checkout")
    ) {
      // Check if cart is visible (scrolled to it)
      if (detector.isCartAreaVisible()) {
        const isAuthenticated = await this.storage.isAuthenticated();
        if (!isAuthenticated) {
          this.showLoginNudge();
        } else {
          this.showAnalyzeNudge();
        }
      }
    } else {
      this.removeNudges();
    }
  }

  private showLoginNudge() {
    if (document.getElementById("fg-nudge-login")) return;
    this.removeNudges();

    const nudge = document.createElement("div");
    nudge.id = "fg-nudge-login";
    nudge.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 2147483646;
      background: #0B2A24;
      color: #E2E8F0;
      padding: 12px 20px;
      border-radius: 12px;
      border: 1px solid #123F36;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      cursor: pointer;
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 14px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 12px;
      animation: fg-fade-in 0.3s ease-out;
    `;
    nudge.innerHTML = `
      <div style="background: rgba(0, 255, 194, 0.1); padding: 6px; border-radius: 50%; display: flex;">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00FFC2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      </div>
      <span>Sign in to Fiscal Guard to analyze cart</span>
      <style>
        @keyframes fg-fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      </style>
    `;
    nudge.onclick = () => {
      alert(
        "Please click the Fiscal Guard extension icon in your toolbar to sign in.",
      );
    };

    document.body.appendChild(nudge);
  }

  private showAnalyzeNudge() {
    if (document.getElementById("fg-nudge-analyze")) return;
    this.removeNudges();

    const btn = document.createElement("button");
    btn.id = "fg-nudge-analyze";
    btn.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 2147483646;
      background: #00FFC2;
      color: #0B2A24;
      border: none;
      padding: 12px 24px;
      border-radius: 50px;
      box-shadow: 0 4px 12px rgba(0, 255, 194, 0.3);
      cursor: pointer;
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 14px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: transform 0.2s;
      animation: fg-fade-in 0.3s ease-out;
    `;
    btn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      Analyze Cart
      <style>
        @keyframes fg-fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      </style>
    `;
    btn.onmouseenter = () => {
      btn.style.transform = "scale(1.05)";
    };
    btn.onmouseleave = () => {
      btn.style.transform = "scale(1)";
    };
    btn.onclick = () => this.handleAnalyzeCart();

    document.body.appendChild(btn);
  }

  private removeNudges() {
    document.getElementById("fg-nudge-login")?.remove();
    document.getElementById("fg-nudge-analyze")?.remove();
  }

  /**
   * Main flow: Analyze cart and display sidebar
   */
  async handleAnalyzeCart() {
    if (this.isProcessing) {
      this.showNotification("Analysis already in progress...", "info");
      return;
    }

    this.isProcessing = true;
    this.removeNudges();

    try {
      // 1. Detect Amazon page
      const detector = new AmazonDetector();
      const pageInfo = detector.detect();

      if (!pageInfo.isAmazon) {
        this.showNotification(
          "This extension only works on Amazon pages",
          "error",
        );
        return;
      }

      if (pageInfo.pageType !== "cart" && pageInfo.pageType !== "checkout") {
        this.showNotification(
          "Please navigate to your cart or checkout page",
          "info",
        );
        return;
      }

      // Check if cart is visible
      if (!detector.isCartAreaVisible()) {
        this.showNotification(
          "Cart area not found. Please scroll to your cart.",
          "info",
        );
        return;
      }

      // 2. Show loading state
      this.showLoadingState();

      // 3. Capture screenshot
      console.log("[Fiscal Guard] Capturing screenshot...");
      const capture = new ScreenshotCapture();
      const screenshot = await capture.captureCartArea();

      // 4. Extract items using backend Vision Agent (secure, server-side)
      console.log("[Fiscal Guard] Extracting items with Vision Agent...");

      const extractionResponse = await this.apiClient.extractCartFromScreenshot(
        screenshot,
        window.location.href,
        pageInfo.pageType,
      );

      if (
        !extractionResponse.success ||
        extractionResponse.items.length === 0
      ) {
        throw new Error(
          extractionResponse.error ||
            "No items found in cart. Please try again.",
        );
      }

      // Log warnings if any
      if (
        extractionResponse.warnings &&
        extractionResponse.warnings.length > 0
      ) {
        console.warn(
          "[Fiscal Guard] Extraction warnings:",
          extractionResponse.warnings,
        );
      }

      // Check validation report
      if (
        extractionResponse.validationReport &&
        !extractionResponse.validationReport.is_valid
      ) {
        console.warn(
          "[Fiscal Guard] Low extraction quality:",
          extractionResponse.validationReport,
        );
        // Optionally show warning to user
        if (extractionResponse.validationReport.recommendations.length > 0) {
          this.showNotification(
            extractionResponse.validationReport.recommendations[0],
            "info",
          );
        }
      }

      console.log(
        `[Fiscal Guard] Extracted ${extractionResponse.items.length} items (quality: ${extractionResponse.extractionQuality}, confidence: ${extractionResponse.confidenceScore})`,
      );

      // 5. Send to backend for decision analysis
      console.log("[Fiscal Guard] Analyzing items...");
      const analysisResults = await this.apiClient.analyzeCart({
        items: extractionResponse.items,
        page_url: window.location.href,
        page_type: pageInfo.pageType,
      });

      // 6. Hide loading, show sidebar
      this.hideLoadingState();
      this.showSidebar(analysisResults);

      console.log("[Fiscal Guard] Analysis complete!");
    } catch (error) {
      console.error("[Fiscal Guard] Error:", error);
      this.hideLoadingState();
      this.showNotification(
        error instanceof Error ? error.message : "An error occurred",
        "error",
      );
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Show sidebar with analysis results
   */
  private showSidebar(analysisResults: any) {
    this.removeNudges();

    // Close existing sidebar if any
    if (this.activeSidebar) {
      this.activeSidebar();
    }

    console.log(analysisResults);

    // Inject new sidebar
    this.activeSidebar = injectFloatingSidebar(analysisResults, this.apiClient);
  }

  /**
   * Show loading overlay
   */
  private showLoadingState() {
    const loadingId = "fiscal-guard-loading";

    // Remove existing if any
    const existing = document.getElementById(loadingId);
    if (existing) {
      existing.remove();
    }

    const loading = document.createElement("div");
    loading.id = loadingId;
    loading.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 2147483646;
      background: #0B2A24;
      border: 1px solid #123F36;
      color: #E2E8F0;
      padding: 24px 32px;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      font-family: system-ui, -apple-system, sans-serif;
    `;

    loading.innerHTML = `
      <div style="
        width: 40px;
        height: 40px;
        border: 4px solid #123F36;
        border-top-color: #00FFC2;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      "></div>
      <div style="
        font-size: 14px;
        color: #E2E8F0;
        font-weight: 500;
      ">Analyzing your cart...</div>
      <style>
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      </style>
    `;

    document.body.appendChild(loading);
  }

  /**
   * Hide loading overlay
   */
  private hideLoadingState() {
    const loading = document.getElementById("fiscal-guard-loading");
    if (loading) {
      loading.remove();
    }
  }

  /**
   * Show notification toast
   */
  private showNotification(
    message: string,
    type: "info" | "error" | "success" = "info",
  ) {
    const notificationId = "fiscal-guard-notification";

    // Remove existing if any
    const existing = document.getElementById(notificationId);
    if (existing) {
      existing.remove();
    }

    const colors = {
      info: { bg: "#3b82f6", text: "#ffffff" },
      error: { bg: "#ef4444", text: "#ffffff" },
      success: { bg: "#22c55e", text: "#ffffff" },
    };

    const notification = document.createElement("div");
    notification.id = notificationId;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 2147483647;
      background: ${colors[type].bg};
      color: ${colors[type].text};
      padding: 16px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 14px;
      max-width: 400px;
      animation: slideInRight 0.3s ease-out;
    `;

    notification.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 20px;">
          ${type === "error" ? "⚠️" : type === "success" ? "✅" : "ℹ️"}
        </span>
        <span>${message}</span>
      </div>
      <style>
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      </style>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }
}

// Initialize extension when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    const extension = new FiscalGuardExtension();
    extension.initialize();
  });
} else {
  const extension = new FiscalGuardExtension();
  extension.initialize();
}
