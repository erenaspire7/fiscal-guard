/**
 * Screenshot capture utility for cart pages
 */

import { AmazonDetector } from "./AmazonDetector";

export class ScreenshotCapture {
  private detector: AmazonDetector;

  constructor() {
    this.detector = new AmazonDetector();
  }

  /**
   * Capture screenshot of current viewport
   * Returns blob that can be sent to Gemini Vision
   */
  async captureCartArea(): Promise<Blob> {
    // Ensure cart is in view
    await this.detector.scrollCartIntoView();

    // Wait for images to load
    await this.waitForImages();

    // Capture current viewport
    const dataUrl = await this.captureVisibleTab();
    return this.dataUrlToBlob(dataUrl);
  }

  /**
   * Capture visible tab using chrome.tabs API
   */
  private async captureVisibleTab(): Promise<string> {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        { action: "capture-screenshot" },
        (response) => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else if (response?.dataUrl) {
            resolve(response.dataUrl);
          } else {
            reject(new Error("Failed to capture screenshot"));
          }
        },
      );
    });
  }

  /**
   * Wait for images to load
   */
  private async waitForImages(): Promise<void> {
    const images = Array.from(document.images);
    const promises = images
      .filter((img) => !img.complete)
      .map(
        (img) =>
          new Promise<void>((resolve) => {
            img.addEventListener("load", () => resolve());
            img.addEventListener("error", () => resolve()); // Resolve even on error
            setTimeout(() => resolve(), 2000); // Timeout after 2s
          }),
      );

    await Promise.all(promises);
  }

  /**
   * Convert data URL to Blob
   */
  private async dataUrlToBlob(dataUrl: string): Promise<Blob> {
    const response = await fetch(dataUrl);
    return await response.blob();
  }

  /**
   * Get estimated screenshot size
   */
  getEstimatedSize(): { width: number; height: number } {
    return {
      width: window.innerWidth,
      height: window.innerHeight,
    };
  }
}
