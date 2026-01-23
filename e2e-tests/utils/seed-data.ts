/**
 * Seed demo data for E2E tests
 *
 * This script creates demo users, budgets, goals, and decisions
 * via the API endpoints, ensuring data consistency.
 */

import axios from "axios";

const API_URL = process.env.API_URL || "http://localhost:8000";

export interface DemoUser {
  email: string;
  password: string;
  fullName: string;
  personaTone: "gentle" | "balanced" | "financial_monk";
  strictnessLevel: number;
  token?: string;
  userId?: string;
}

export const DEMO_USERS: Record<string, DemoUser> = {
  sarah: {
    email: "demo+sarah@fiscalguard.app",
    password: "demo123",
    fullName: "Sarah Chen",
    personaTone: "financial_monk",
    strictnessLevel: 9,
  },
  alex: {
    email: "demo+alex@fiscalguard.app",
    password: "demo123",
    fullName: "Alex Sterling",
    personaTone: "balanced",
    strictnessLevel: 5,
  },
  marcus: {
    email: "demo+marcus@fiscalguard.app",
    password: "demo123",
    fullName: "Marcus Wu",
    personaTone: "gentle",
    strictnessLevel: 2,
  },
};

/**
 * Register a demo user and get auth token
 * Tries to login first, only registers if user doesn't exist
 */
async function registerUser(user: DemoUser): Promise<string> {
  // Try to login first (in case user already exists)
  try {
    const loginResponse = await axios.post(`${API_URL}/auth/login`, {
      email: user.email,
      password: user.password,
    });
    console.log(`  ✓ User already exists, logged in`);
    return loginResponse.data.access_token;
  } catch (loginError: any) {
    // User doesn't exist or wrong credentials, try to register
    if (loginError.response?.status === 401) {
      try {
        const response = await axios.post(`${API_URL}/auth/register`, {
          email: user.email,
          password: user.password,
          full_name: user.fullName,
        });

        const token = response.data.access_token;

        // Update user persona settings
        await axios.patch(
          `${API_URL}/users/me`,
          {
            persona_tone: user.personaTone,
            strictness_level: user.strictnessLevel,
          },
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );

        console.log(`  ✓ User registered successfully`);
        return token;
      } catch (registerError: any) {
        throw registerError;
      }
    }
    throw loginError;
  }
}

/**
 * Get existing budgets for a user
 */
async function getBudgets(token: string) {
  const response = await axios.get(`${API_URL}/budgets`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}

/**
 * Create a budget for a user (idempotent - checks if exists first)
 */
async function createBudget(token: string, data: any) {
  const existing = await getBudgets(token);
  const exists = existing.some((b: any) => b.name === data.name);

  if (exists) {
    console.log(`    ⏭️  Budget "${data.name}" already exists, skipping`);
    return { data: existing.find((b: any) => b.name === data.name) };
  }

  return axios.post(`${API_URL}/budgets`, data, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

/**
 * Get existing goals for a user
 */
async function getGoals(token: string) {
  const response = await axios.get(`${API_URL}/goals`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}

/**
 * Create a goal for a user (idempotent - checks if exists first)
 */
async function createGoal(token: string, data: any) {
  const existing = await getGoals(token);
  const exists = existing.some((g: any) => g.goal_name === data.goal_name);

  if (exists) {
    console.log(`    ⏭️  Goal "${data.goal_name}" already exists, skipping`);
    return { data: existing.find((g: any) => g.goal_name === data.goal_name) };
  }

  return axios.post(`${API_URL}/goals`, data, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

/**
 * Get existing decisions for a user
 */
async function getDecisions(token: string) {
  const response = await axios.get(`${API_URL}/decisions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}

/**
 * Create a purchase decision (idempotent - checks if exists first)
 */
async function createDecision(token: string, data: any) {
  const existing = await getDecisions(token);

  const exists = existing.some(
    (d: any) =>
      d.item_name === data.item_name &&
      parseFloat(d.amount) === parseFloat(data.amount),
  );

  if (exists) {
    console.log(
      `    ⏭️  Decision "${data.item_name}" already exists, skipping`,
    );
    return {
      data: existing.find(
        (d: any) =>
          d.item_name === data.item_name &&
          parseFloat(d.amount) === parseFloat(data.amount),
      ),
    };
  }

  return axios.post(`${API_URL}/decisions`, data, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

/**
 * Add feedback to a decision (idempotent - checks if feedback exists)
 */
async function addFeedback(token: string, decisionId: string, data: any) {
  // Get the decision to check if it already has feedback
  const decisions = await getDecisions(token);
  const decision = decisions.find((d: any) => d.decision_id === decisionId);

  if (
    decision?.actual_purchase !== null &&
    decision?.actual_purchase !== undefined
  ) {
    console.log(
      `    ⏭️  Feedback for "${decision.item_name}" already exists, skipping`,
    );
    return { data: decision };
  }

  return axios.post(`${API_URL}/decisions/${decisionId}/feedback`, data, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

/**
 * Seed Sarah's data (Impulsive Buyer)
 */
async function seedSarah(token: string) {
  console.log("  📊 Creating Sarah's budget...");
  await createBudget(token, {
    name: "January 2026 Budget",
    total_monthly: 3500,
    period_start: "2026-01-01",
    period_end: "2026-01-31",
    categories: {
      groceries: { limit: 600, spent: 520 },
      dining: { limit: 200, spent: 280 },
      shopping: { limit: 300, spent: 450 },
      entertainment: { limit: 150, spent: 180 },
      transportation: { limit: 400, spent: 320 },
      utilities: { limit: 250, spent: 250 },
    },
  });

  console.log("  🎯 Creating Sarah's goals...");
  await createGoal(token, {
    goal_name: "Emergency Fund",
    target_amount: 10000,
    current_amount: 2800,
    priority: "high",
    deadline: "2026-12-31",
  });

  await createGoal(token, {
    goal_name: "House Down Payment",
    target_amount: 50000,
    current_amount: 15000,
    priority: "high",
    deadline: "2028-06-30",
  });

  console.log("  🛍️ Creating Sarah's decisions...");

  // Recent decision (no feedback)
  await createDecision(token, {
    item_name: "Designer Handbag",
    amount: 450,
    category: "shopping",
    reason: "Saw it on Instagram, looks amazing",
    urgency: "low",
  });

  // Past decisions with feedback
  const shoeDecision = await createDecision(token, {
    item_name: "Designer Shoes",
    amount: 280,
    category: "shopping",
    reason: "Limited edition release",
    urgency: "high",
  });

  await addFeedback(token, shoeDecision.data.decision_id, {
    actual_purchase: true,
    regret_level: 9,
    feedback: "Barely wore them, waste of money",
  });

  const dinnerDecision = await createDecision(token, {
    item_name: "Fancy Restaurant Dinner",
    amount: 120,
    category: "dining",
    reason: "Celebrating friend's birthday",
    urgency: "medium",
  });

  await addFeedback(token, dinnerDecision.data.decision_id, {
    actual_purchase: true,
    regret_level: 3,
    feedback: "Worth it for the memories",
  });
}

/**
 * Seed Alex's data (Balanced Spender)
 */
async function seedAlex(token: string) {
  console.log("  📊 Creating Alex's budget...");
  await createBudget(token, {
    name: "January 2026 Budget",
    total_monthly: 4500,
    period_start: "2026-01-01",
    period_end: "2026-01-31",
    categories: {
      groceries: { limit: 700, spent: 450 },
      dining: { limit: 300, spent: 180 },
      shopping: { limit: 400, spent: 320 },
      entertainment: { limit: 300, spent: 150 },
      transportation: { limit: 500, spent: 400 },
      utilities: { limit: 300, spent: 300 },
    },
  });

  console.log("  🎯 Creating Alex's goals...");
  await createGoal(token, {
    goal_name: "Vacation Fund",
    target_amount: 5000,
    current_amount: 3500,
    priority: "medium",
    deadline: "2026-08-01",
  });

  console.log("  🎵 Creating Alex's decisions...");
  const concertDecision = await createDecision(token, {
    item_name: "Concert Tickets",
    amount: 150,
    category: "entertainment",
    reason: "Favorite band's tour",
    urgency: "medium",
  });

  await addFeedback(token, concertDecision.data.decision_id, {
    actual_purchase: true,
    regret_level: 2,
    feedback: "Amazing experience!",
  });
}

/**
 * Seed Marcus's data (Financial Monk)
 */
async function seedMarcus(token: string) {
  console.log("  📊 Creating Marcus's budget...");
  await createBudget(token, {
    name: "January 2026 Budget",
    total_monthly: 2500,
    period_start: "2026-01-01",
    period_end: "2026-01-31",
    categories: {
      groceries: { limit: 400, spent: 280 },
      dining: { limit: 50, spent: 20 },
      shopping: { limit: 100, spent: 45 },
      entertainment: { limit: 50, spent: 0 },
      transportation: { limit: 300, spent: 250 },
      utilities: { limit: 200, spent: 200 },
    },
  });

  console.log("  🎯 Creating Marcus's goals...");
  await createGoal(token, {
    goal_name: "Early Retirement Fund",
    target_amount: 500000,
    current_amount: 125000,
    priority: "high",
    deadline: "2035-12-31",
  });

  console.log("  📚 Creating Marcus's decisions...");
  const bookDecision = await createDecision(token, {
    item_name: "Investment Book",
    amount: 25,
    category: "shopping",
    reason: "Financial education",
    urgency: "low",
  });

  await addFeedback(token, bookDecision.data.decision_id, {
    actual_purchase: true,
    regret_level: 1,
    feedback: "Learned valuable strategies",
  });
}

/**
 * Main seed function
 */
export async function seedDemoData(): Promise<Record<string, DemoUser>> {
  console.log("🌱 Seeding demo data via API...\n");

  const seededUsers: Record<string, DemoUser> = {};

  try {
    // Sarah
    console.log("👤 Setting up Sarah Chen (Impulsive Buyer)...");
    const sarahToken = await registerUser(DEMO_USERS.sarah);
    await seedSarah(sarahToken);
    seededUsers.sarah = { ...DEMO_USERS.sarah, token: sarahToken };
    console.log("  ✅ Sarah complete\n");

    // Alex
    console.log("👤 Setting up Alex Sterling (Balanced Spender)...");
    const alexToken = await registerUser(DEMO_USERS.alex);
    await seedAlex(alexToken);
    seededUsers.alex = { ...DEMO_USERS.alex, token: alexToken };
    console.log("  ✅ Alex complete\n");

    // Marcus
    console.log("👤 Setting up Marcus Wu (Financial Monk)...");
    const marcusToken = await registerUser(DEMO_USERS.marcus);
    await seedMarcus(marcusToken);
    seededUsers.marcus = { ...DEMO_USERS.marcus, token: marcusToken };
    console.log("  ✅ Marcus complete\n");

    console.log("✨ Demo data seeding complete!\n");
    console.log("📝 Demo Accounts:");
    console.log(
      "  - Sarah: demo+sarah@fiscalguard.app / demo123 (Financial Monk 9/10)",
    );
    console.log(
      "  - Alex: demo+alex@fiscalguard.app / demo123 (Balanced 5/10)",
    );
    console.log(
      "  - Marcus: demo+marcus@fiscalguard.app / demo123 (Gentle 2/10)\n",
    );

    return seededUsers;
  } catch (error: any) {
    console.error("❌ Error seeding data:", error.message);
    if (error.response) {
      console.error("   Response:", error.response.data);
    }
    throw error;
  }
}

/**
 * Login and get token for a demo user
 */
export async function loginDemoUser(
  email: string,
  password: string,
): Promise<string> {
  const response = await axios.post(`${API_URL}/auth/login`, {
    email,
    password,
  });
  return response.data.access_token;
}

// Run if executed directly
if (require.main === module) {
  seedDemoData()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}
