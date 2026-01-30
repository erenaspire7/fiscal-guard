/**
 * Chrome storage wrapper for managing extension data
 */

export class StorageManager {
  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const result = await chrome.storage.local.get(["authToken"]);
    return !!result.authToken;
  }

  /**
   * Get authentication token
   */
  async getAuthToken(): Promise<string | null> {
    const result = await chrome.storage.local.get(["authToken"]);
    return result.authToken || null;
  }

  /**
   * Set authentication token
   */
  async setAuthToken(token: string): Promise<void> {
    await chrome.storage.local.set({ authToken: token });
  }

  /**
   * Clear authentication token
   */
  async clearAuthToken(): Promise<void> {
    await chrome.storage.local.remove(["authToken"]);
  }

  /**
   * Get user info
   */
  async getUserInfo(): Promise<any> {
    const result = await chrome.storage.local.get(["userInfo"]);
    return result.userInfo || null;
  }

  /**
   * Set user info
   */
  async setUserInfo(userInfo: any): Promise<void> {
    await chrome.storage.local.set({ userInfo });
  }

  /**
   * Get screenshot consent
   */
  async getScreenshotConsent(): Promise<boolean> {
    const result = await chrome.storage.local.get(["screenshotConsent"]);
    return result.screenshotConsent || false;
  }

  /**
   * Set screenshot consent
   */
  async setScreenshotConsent(consent: boolean): Promise<void> {
    await chrome.storage.local.set({ screenshotConsent: consent });
  }

  /**
   * Clear all storage
   */
  async clearAll(): Promise<void> {
    await chrome.storage.local.clear();
    await chrome.storage.sync.clear();
  }
}
