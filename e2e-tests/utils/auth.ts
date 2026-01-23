/**
 * Authentication utilities for E2E tests
 */

import { Page } from '@playwright/test';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export interface AuthTokens {
  accessToken: string;
  tokenType: string;
}

/**
 * Login via API and get JWT token
 */
export async function loginViaAPI(email: string, password: string): Promise<string> {
  const response = await axios.post(`${API_URL}/auth/login`, {
    email,
    password,
  });
  return response.data.access_token;
}

/**
 * Inject auth token into browser storage
 * This bypasses the login UI and directly sets the auth state
 */
export async function injectAuthToken(page: Page, token: string) {
  await page.context().addCookies([
    {
      name: 'auth_token',
      value: token,
      domain: 'localhost',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax',
    },
  ]);

  // Also inject into localStorage if the app uses it
  await page.addInitScript((token) => {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('token', token);
  }, token);
}

/**
 * Setup authenticated session for a user
 */
export async function setupAuthenticatedSession(
  page: Page,
  email: string,
  password: string
): Promise<string> {
  const token = await loginViaAPI(email, password);
  await injectAuthToken(page, token);
  return token;
}

/**
 * Get user info from token
 */
export async function getUserInfo(token: string) {
  const response = await axios.get(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const cookies = await page.context().cookies();
  const authCookie = cookies.find((c) => c.name === 'auth_token');

  if (!authCookie) {
    const token = await page.evaluate(() => {
      return localStorage.getItem('auth_token') || localStorage.getItem('token');
    });
    return !!token;
  }

  return true;
}

/**
 * Logout by clearing auth state
 */
export async function logout(page: Page) {
  await page.context().clearCookies();
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}
