# Fiscal Guard E2E Tests

End-to-end testing suite for Fiscal Guard using Playwright. Tests real user scenarios with seeded demo data.

## Overview

This test suite validates the complete user journey for three personas:
- **Sarah** (Shopping Addiction): Over-budget warnings, impulse purchase tracking, regret patterns
- **Alex** (Balanced Lifestyle): Budget compliance, goal progress, balanced decision-making
- **Marcus** (Extreme Discipline): Strict budget adherence, high savings rate, disciplined behavior

## Prerequisites

- Node.js 18+ installed
- Docker and Docker Compose (tests are designed to run in containerized environment)
- Backend API running on `http://localhost:8000`
- Frontend UI running on `http://localhost:5173`

## Installation

```bash
cd e2e-tests
npm install
npx playwright install
```

## Configuration

Create a `.env` file in the `e2e-tests` directory:

```env
API_URL=http://localhost:8000
UI_URL=http://localhost:5173
GOOGLE_API_KEY=your-google-api-key-here
```

> **Important**: The `GOOGLE_API_KEY` is required for the AI decision agent to work during test data seeding. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

> **Note**: Tests are designed to run within Docker containers where the database configuration is handled automatically.

## Running Tests

### Recommended: Use the test script (from project root)

The easiest way to run tests is using the provided script, which handles starting/stopping services:

```bash
# From project root directory
./scripts/test-e2e.sh                    # Run all tests
./scripts/test-e2e.sh sarah              # Run Sarah's tests only
./scripts/test-e2e.sh alex               # Run Alex's tests only
./scripts/test-e2e.sh marcus             # Run Marcus's tests only

# Reset database before running tests (clean slate)
./scripts/test-e2e.sh --reset-db         # Run all tests with fresh DB
./scripts/test-e2e.sh --reset-db sarah   # Run Sarah's tests with fresh DB
```

The script will:
1. Load environment variables from `.env`
2. Optionally reset the database (with `--reset-db` flag)
3. Run database migrations
4. Start API and UI servers
5. Wait for services to be ready
6. Run the tests
7. Clean up (stop servers) when done

**Tip:** Use `--reset-db` when you have duplicate data or want to start fresh. This drops all tables and recreates them from scratch.

### Manual testing (if servers are already running)

If you prefer to manage the servers yourself:

```bash
cd e2e-tests

# All tests
yarn test

# Specific scenario
yarn test:sarah    # Sarah's shopping addiction tests
yarn test:alex     # Alex's balanced lifestyle tests
yarn test:marcus   # Marcus's extreme discipline tests

# Interactive UI mode
yarn test:ui

# Seed demo data only
yarn seed
```

## Project Structure

```
e2e-tests/
├── tests/
│   ├── scenario-sarah.spec.ts   # 8 tests for Sarah persona
│   ├── scenario-alex.spec.ts    # 5 tests for Alex persona
│   └── scenario-marcus.spec.ts  # 6 tests for Marcus persona
├── utils/
│   ├── seed-data.ts             # API-based demo data seeding
│   ├── auth.ts                  # Token injection & authentication
│   └── test-helpers.ts          # Common test utilities
├── playwright.config.ts         # Playwright configuration
└── package.json                 # Dependencies & scripts
```

## How It Works

### 1. Data Seeding
Tests use API-based seeding to create realistic demo data:
- Registers users via `/auth/register`
- Creates budgets, goals, and decisions via API endpoints
- Returns authentication tokens for each user

### 2. Authentication
Tests bypass the login UI using token injection:
```typescript
await setupAuthenticatedSession(page, 'sarah@example.com', 'demo123');
```

This injects JWT tokens into both localStorage and cookies.

### 3. Test Execution
Tests run sequentially (single worker) to avoid database conflicts:
- Each test navigates to specific pages
- Validates UI elements and data display
- Tests user interactions (clicks, form submissions)
- Verifies API integration (feedback, goal progress)

## Test Scenarios

### Sarah (Shopping Addiction)
- Dashboard shows over-budget warnings
- Insights display regret patterns
- Vault shows savings goals with progress
- Can add progress to goals
- Can provide feedback on decisions
- Agent suggestions appear correctly
- Chat input works for new decisions
- Feedback updates decision cards

### Alex (Balanced Lifestyle)
- Dashboard shows balanced spending
- Insights display moderate regret patterns
- Multiple budget categories visible
- Goal progress tracking works
- Vault displays both budgets and goals

### Marcus (Extreme Discipline)
- Dashboard shows strict budget adherence
- Insights display low/no regret
- High goal progress visible
- Agent suggestions reflect disciplined persona
- Vault shows advanced financial tracking

## Key Features

### Sequential Execution
Tests run one at a time to ensure database consistency:
```typescript
fullyParallel: false,
workers: 1,
```

### Server Management
The `test-e2e.sh` script handles starting and stopping the API and UI servers:
- Loads environment variables from `.env`
- Runs database migrations
- Starts API server on port 8000
- Starts UI server on port 5173
- Waits for health checks
- Runs tests
- Cleans up servers on exit

### Docker Environment
Tests are designed to run within Docker containers where database configuration and service orchestration are handled automatically.

### Test Utilities

#### `waitForLoadingComplete(page)`
Waits for loading spinners to disappear before assertions.

#### `clickButton(page, text)`
Clicks buttons with retry logic for flaky tests.

#### `setupAuthenticatedSession(page, email, password)`
Handles complete authentication flow with token injection.

## Troubleshooting

### Tests fail with "Element not visible"
- Increase timeout values in `playwright.config.ts`
- Check if loading states are properly handled
- Verify UI server is running on correct port

### Database conflicts
- Ensure `workers: 1` in config (sequential execution)
- Check if `TEST_DATABASE_URL` points to isolated test DB
- Delete `test.db` and rerun tests

### Authentication errors
- Verify API server is running on `http://localhost:8000`
- Check if `/auth/login` and `/auth/register` endpoints work
- Ensure demo passwords are "demo123"

### Seeding fails
- Check API server logs for errors
- Verify all required endpoints exist
- Ensure database migrations are up to date

## Demo User Credentials

All demo users have password: `demo123`

- Sarah: `sarah@example.com`
- Alex: `alex@example.com`
- Marcus: `marcus@example.com`

## Notes

- Tests use API-based seeding (not direct DB manipulation) to ensure proper validation
- Token injection bypasses OAuth flow for faster test execution
- Each test scenario is independent and can run in isolation
- Loading states are handled automatically with custom wait utilities
- Tests validate both UI rendering and API integration

## TODO

- Add UI login form tests (currently bypassed via token injection)
- Add tests for budget creation flow
- Add tests for goal creation flow
- Add tests for profile/persona customization
- Add performance/accessibility testing
- Add visual regression testing
