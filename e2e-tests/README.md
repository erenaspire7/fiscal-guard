# E2E Tests v2 (Python)

Python-based E2E testing and data seeding for Fiscal Guard.

## Features

- **Fast Database Seeding**: Direct database inserts (no API calls, no AI evaluation)
- **Browser E2E Tests**: pytest + Playwright for UI testing with video recording
- **API E2E Tests**: pytest-based tests with httpx for API testing
- **Realistic Demo Data**: Pre-populated with thoughtful decision patterns

## Setup

Install dependencies:
```bash
cd e2e-tests-v2
uv sync
```

Install Playwright browsers (required for UI tests):
```bash
uv run playwright install
```

## Usage

### Seed Database

Seed demo data directly to the database:
```bash
cd e2e-tests-v2
uv run python seed.py
```

Or from the project root using the reset-and-seed script:
```bash
./scripts/reset-and-seed.sh
```

### Run Tests

Run all tests:
```bash
uv run pytest
```

Run only UI tests (with video recording):
```bash
uv run pytest tests/test_scenario_*.py
```

Run only API tests:
```bash
uv run pytest tests/test_api.py
```

Run specific scenario:
```bash
uv run pytest tests/test_scenario_sarah.py
```

Run with coverage:
```bash
uv run pytest --cov=. --cov-report=html
```

Run in headed mode (see browser):
```bash
uv run pytest --headed tests/test_scenario_sarah.py
```

Videos are saved to `videos/` directory by default.

## Demo Data

The seed script creates:

### Sarah Chen (Impulsive → Improving)
- **Email**: demo+sarah@fiscalguard.app
- **Password**: demo123
- **Persona**: Financial Monk (9/10 strictness)
- **Budget**: Resets 1st of month
- **Pattern**: 36 decisions over 6 months showing improvement from overspending to disciplined

### Future: Alex & Marcus
Structure ready to add:
- Alex: Balanced spender (24 decisions)
- Marcus: Financial Monk (18 decisions)

## Performance

- **Before (TypeScript + API)**: 5-10 minutes (78 AI evaluations)
- **After (Python + Direct DB)**: 2-3 seconds
- **Speed improvement**: ~100-200x faster

## Structure

```
e2e-tests-v2/
├── utils/
│   ├── __init__.py
│   ├── seed_data.py      # Database seeding script
│   ├── auth.py           # Authentication utilities
│   └── test_helpers.py   # Playwright test helpers
├── tests/
│   ├── __init__.py
│   ├── test_api.py              # API E2E tests
│   ├── test_scenario_sarah.py   # Sarah's shopping addiction scenario
│   ├── test_scenario_marcus.py  # Marcus's extreme discipline scenario
│   └── test_scenario_alex.py    # Alex's balanced lifestyle scenario
├── conftest.py           # Pytest configuration and fixtures
├── pyproject.toml        # Dependencies and config
├── seed.py               # Entry point for seeding
└── README.md
```

## Test Scenarios

### Sarah Chen - Shopping Addiction
- 8 tests covering over-budget warnings, regret patterns, strict agent recommendations
- Demonstrates Financial Monk persona (9/10 strictness)
- Tests satisfaction rating on past decisions
- Full user journey: Dashboard → Chat → Insights → Vault

### Marcus Wu - Extreme Discipline  
- 6 tests covering excellent budget status, minimal spending patterns
- Demonstrates Gentle persona (2/10 strictness)
- Tests large retirement fund contributions
- Investment-focused decision making

### Alex Sterling - Balanced Lifestyle
- 5 tests covering healthy budget management
- Demonstrates Balanced persona (5/10 strictness)
- Tests vacation fund management
- Positive feedback on entertainment purchases

## Why Python?

1. **Shared Language**: Same as the API (core/api)
2. **Direct DB Access**: Use SQLAlchemy models directly
3. **Better Tooling**: pytest, httpx, coverage
4. **No API Required**: Seed without starting the server
5. **Faster**: Direct inserts vs API calls
