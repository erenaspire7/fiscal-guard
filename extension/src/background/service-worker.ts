/**
 * Background service worker for Fiscal Guard extension
 */

// Polyfill process to prevent ReferenceError from dependencies expecting Node.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
if (typeof (globalThis as any).process === "undefined") {
  (globalThis as any).process = {
    env: { NODE_ENV: "production" },
    nextTick: (fn: () => void) => setTimeout(fn, 0),
  };
}

// Polyfill document to prevent ReferenceError from dependencies expecting DOM
if (typeof document === "undefined") {
  // @ts-ignore
  self.document = {
    createElement: () => ({}) as any,
    addEventListener: () => {},
    head: { appendChild: () => ({}) as any },
  } as any;
}

import { logout } from "./auth";
import { StorageManager } from "../shared/storage";
import { MESSAGE_TYPES } from "../shared/constants";

const storage = new StorageManager();

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // Handle async operations
  (async () => {
    try {
      switch (request.action) {
        case MESSAGE_TYPES.CAPTURE_SCREENSHOT:
          // Capture visible tab
          if (sender.tab?.id) {
            const dataUrl = await chrome.tabs.captureVisibleTab(
              sender.tab.windowId,
              { format: "png" },
            );
            sendResponse({ success: true, dataUrl });
          } else {
            sendResponse({ success: false, error: "No tab ID" });
          }
          break;

        case MESSAGE_TYPES.GET_AUTH_TOKEN:
          // Get current auth token
          const token = await storage.getAuthToken();
          sendResponse({ success: true, token });
          break;

        case MESSAGE_TYPES.LOGOUT:
          // Logout user
          await logout();
          sendResponse({ success: true });
          break;

        default:
          sendResponse({ success: false, error: "Unknown action" });
      }
    } catch (error) {
      console.error("Error handling message:", error);
      sendResponse({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      });
    }
  })();

  // Return true to indicate we'll send a response asynchronously
  return true;
});

// Initialize extension
console.log("Fiscal Guard extension initialized");
