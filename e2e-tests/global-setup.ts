/**
 * Global setup for Playwright tests
 * Runs once before all tests to seed demo data
 */

import { seedDemoData } from "./utils/seed-data";
import axios from "axios";

const API_URL = process.env.API_URL || "http://localhost:8000";
const MAX_RETRIES = 30;
const RETRY_DELAY = 1000;

/**
 * Wait for API to be ready
 */
async function waitForAPI() {
  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      await axios.get(`${API_URL}/health`);
      console.log("✓ API is ready");
      return;
    } catch (error) {
      if (i < MAX_RETRIES - 1) {
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      }
    }
  }
  throw new Error("API failed to start");
}

async function globalSetup() {
  console.log("⏳ Waiting for API to be ready...");
  await waitForAPI();

  console.log("🌱 Seeding demo data for E2E tests...");

  try {
    const users = await seedDemoData();
    console.log("✓ Demo data seeded successfully");
    console.log(`✓ Created users: ${Object.keys(users).join(", ")}`);
  } catch (error: any) {
    console.error("✗ Failed to seed demo data:", error.message);
    if (error.response) {
      console.error("   Response status:", error.response.status);
      console.error("   Response data:", error.response.data);
    }
    throw error;
  }
}

export default globalSetup;
