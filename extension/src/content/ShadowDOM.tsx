/**
 * Shadow DOM wrapper for style isolation
 */

import { createRoot, Root } from "react-dom/client";
import { FloatingSidebar } from "./FloatingSidebar";
import type { CartAnalysisResponse, ChatResponse } from "../shared/types";
import { ApiClient } from "../shared/api-client";

/**
 * Inject floating sidebar with Shadow DOM isolation
 */
export function injectFloatingSidebar(
  analysisResults: CartAnalysisResponse,
  apiClient: ApiClient,
): () => void {
  if (!document.body) {
    console.warn("[Fiscal Guard] document.body not ready");
    return () => {};
  }

  // Create shadow host
  const shadowHost = document.createElement("div");
  shadowHost.id = "fiscal-guard-root";
  shadowHost.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 2147483647;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  `;

  document.body.appendChild(shadowHost);

  // Attach shadow DOM (isolates styles)
  const shadowRoot = shadowHost.attachShadow({ mode: "open" });

  // Inject styles
  const styleElement = document.createElement("style");
  styleElement.textContent = getStyles();
  shadowRoot.appendChild(styleElement);

  // Create container
  const container = document.createElement("div");
  container.id = "fg-app-container";
  shadowRoot.appendChild(container);

  if (!container || container.nodeType !== Node.ELEMENT_NODE) {
    console.error("[Fiscal Guard] Invalid container for React root");
    shadowHost.remove();
    return () => {};
  }

  // Render React component
  let root: Root;
  try {
    root = createRoot(container);
  } catch (error) {
    console.error("[Fiscal Guard] Failed to create React root:", error);
    shadowHost.remove();
    return () => {};
  }

  const handleChatMessage = async (
    message: string,
    history: any[],
  ): Promise<ChatResponse> => {
    return await apiClient.sendChatMessage(
      message,
      analysisResults.conversation_id,
      history,
    );
  };

  const handleClose = () => {
    root.unmount();
    shadowHost.remove();
  };

  root.render(
    <FloatingSidebar
      analysisResults={analysisResults}
      onChatMessage={handleChatMessage}
      onClose={handleClose}
    />,
  );

  // Return cleanup function
  return () => {
    root.unmount();
    shadowHost.remove();
  };
}

/**
 * Get CSS styles for shadow DOM
 * These are isolated from the host page
 */
function getStyles(): string {
  return `
    /* Reset base styles */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    /* Sidebar container */
    .fg-sidebar {
      width: 400px;
      height: auto;
      max-height: 800px;
      background: #0f1115; /* Very dark background */
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px #1f2937;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #e2e8f0;
      animation: slideIn 0.3s ease-out;
    }

    /* Header */
    .fg-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: #0f1115;
      color: #ffffff;
      flex-shrink: 0;
    }

    .fg-header-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 600;
      font-size: 15px;
      letter-spacing: 0.5px;
    }

    .fg-logo-icon {
      color: #10b981; /* Green accent */
      display: flex;
      align-items: center;
    }

    .fg-close-btn {
      background: transparent;
      border: none;
      color: #9ca3af;
      cursor: pointer;
      padding: 4px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }

    .fg-close-btn:hover {
      background: rgba(255,255,255,0.1);
      color: white;
    }

    /* Scrollable content */
    .fg-content {
      flex: 1;
      overflow-y: auto;
      padding: 0 20px 20px 20px;
    }

    .fg-content::-webkit-scrollbar {
      width: 6px;
    }

    .fg-content::-webkit-scrollbar-track {
      background: transparent;
    }

    .fg-content::-webkit-scrollbar-thumb {
      background: #374151;
      border-radius: 3px;
    }

    /* Score Card */
    .fg-score-card {
      border-radius: 12px;
      padding: 30px 20px;
      text-align: center;
      color: white;
      margin-bottom: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    /* Score Colors */
    .bg-red {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    .bg-orange {
      background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
    }
    .bg-yellow {
      background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
    }
    .bg-green {
      background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    }

    .fg-score-display {
      display: flex;
      align-items: baseline;
      justify-content: center;
    }

    .fg-score-number {
      font-size: 56px;
      font-weight: 800;
      line-height: 1;
    }

    .fg-score-total {
      font-size: 24px;
      font-weight: 500;
      opacity: 0.8;
      margin-left: 2px;
    }

    .fg-score-label {
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-top: 4px;
      opacity: 0.9;
    }

    /* Recommendation Text */
    .fg-recommendation-text {
      font-size: 14px;
      line-height: 1.5;
      color: #9ca3af; /* muted text */
      text-align: center;
      margin-bottom: 20px;
    }

    /* Total Amount */
    .fg-total-display {
      font-size: 18px;
      font-weight: 700;
      text-align: center;
      color: white;
      margin-bottom: 24px;
    }

    /* Section Header */
    .fg-section-header {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #6b7280;
      margin-bottom: 12px;
    }

    /* Item Cards */
    .fg-items-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .fg-item-card {
      background: #181a20; /* Slightly lighter than bg */
      border: 1px solid #272a30;
      border-radius: 12px;
      padding: 16px;
      transition: border-color 0.2s;
    }

    .fg-item-card:hover {
      border-color: #374151;
    }

    .fg-item-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }

    .fg-item-main {
      flex: 1;
      margin-right: 12px;
    }

    .fg-item-name {
      font-size: 14px;
      font-weight: 600;
      color: white;
      margin-bottom: 4px;
      line-height: 1.4;
    }

    .fg-item-calc {
      font-size: 12px;
      color: #9ca3af;
    }

    .fg-item-badge {
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 4px;
      color: white;
      white-space: nowrap;
    }

    .fg-item-reasoning {
      font-size: 13px;
      line-height: 1.5;
      color: #d1d5db;
      border-top: 1px solid #272a30;
      padding-top: 12px;
    }

    /* Chat Section */
    .fg-chat-history {
      margin-top: 24px;
      padding-top: 24px;
      border-top: 1px solid #1f2937;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .fg-chat-message {
      display: flex;
    }

    .fg-chat-message.user {
      justify-content: flex-end;
    }

    .fg-chat-bubble {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 13px;
      line-height: 1.5;
    }

    .fg-chat-message.user .fg-chat-bubble {
      background: #11B981;
      color: white;
    }

    .fg-chat-message.assistant .fg-chat-bubble {
      background: #272a30;
      color: #e5e7eb;
    }

    /* Chat Input */
    .fg-chat-input-container {
      padding: 16px 20px;
      background: #0f1115;
      border-top: 1px solid #1f2937;
    }

    .fg-input-wrapper {
      background: #181a20;
      border: 1px solid #272a30;
      border-radius: 8px;
      display: flex;
      align-items: center;
      padding: 6px 6px 6px 12px;
      transition: border-color 0.2s;
    }

    .fg-input-wrapper:focus-within {
      border-color: #4b5563;
    }

    .fg-chat-input {
      flex: 1;
      background: transparent;
      border: none;
      color: white;
      font-size: 13px;
      outline: none;
      min-width: 0;
    }

    .fg-chat-input::placeholder {
      color: #6b7280;
    }

    .fg-input-arrow-btn {
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      color: #9ca3af;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .fg-input-arrow-btn:hover:not(:disabled) {
      background: #272a30;
      color: white;
    }

    .fg-input-arrow-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* Animations */
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(20px) scale(0.98);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }
  `;
}
