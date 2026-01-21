# Fiscal Guard

**Your AI Financial Companion - Prevent Buyer's Remorse Before It Happens**

[![Status](https://img.shields.io/badge/status-MVP_Complete-success)](https://github.com/yourusername/fiscal-guard)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🎯 What is Fiscal Guard?

Fiscal Guard is an AI-powered financial decision assistant that helps you make smarter purchasing decisions by analyzing your budget, goals, and spending patterns **before** you buy.

Unlike traditional budgeting apps that show you what you overspent *after the fact*, Fiscal Guard intervenes at the moment of decision with personalized insights powered by:

- **Multi-Agent AI System** built with [Strands](https://strands.ai) + Google Gemini
- **Pattern Learning** that gets smarter from your feedback
- **Full Observability** with [Opik](https://www.opik.ai) tracing and evaluation
- **Privacy-First Design** with automatic PII redaction

### The Problem

Americans spend an average of **$21,000/year** on impulse purchases they later regret. Traditional budgeting tools are passive—they tell you after you've blown your budget.

### Our Solution

**Active intervention:** Chat with AI before making a purchase. Get a Decision Score (1-10) with reasoning that considers:
- Your current budget status
- Impact on your financial goals
- Your historical spending patterns
- Your past regrets in similar categories

---

## ✨ Key Features

### 🤖 Intelligent Decision Agent

Ask: *"Should I buy this $200 jacket?"*

Get a comprehensive analysis that includes:
- **Decision Score** (1-10 scale)
- **Budget Impact** - How this affects your spending limits
- **Goal Analysis** - Delays to your financial goals
- **Pattern Insights** - Learns from your past decisions and regrets
- **Personalized Recommendation** - Clear, actionable advice

### 🧠 Pattern Learning System

The AI learns from every decision you make:
- Tracks which purchases you later regret
- Identifies spending triggers (expensive clothing, late-night shopping)
- Warns you about repeated mistakes
- Celebrates proven good decisions

**Example:** *"WARNING: You've regretted 4 out of 5 expensive clothing purchases. Last time you bought designer jeans for $250, you rated your regret 8/10."*

### 📊 Budget & Goals Management

- Create budgets with category-based limits
- Track multiple financial goals with priorities
- Monitor progress toward goals
- Get alerts when approaching limits
- AI-powered chat import using natural language

### 🔒 Privacy & Observability

- **Automatic PII Redaction** - User IDs, emails, exact amounts protected
- **Full Tracing** - Every decision generates 7+ Opik traces
- **GDPR Compliant** - Privacy built-in from day one
- **Performance Monitoring** - Track latency, token usage, decision quality

---

## 🏗️ Architecture

```
User Request (POST /decisions)
    ↓
[JWT Authentication]
    ↓
Decision Service + Opik Tracing
    ↓
Decision Agent (Strands + Gemini 2.0 Flash)
    ↓
┌─────────────────────────────────────────────┐
│  Tool 1: check_budget          ~150ms      │
│  Tool 2: check_goals           ~200ms      │
│  Tool 3: analyze_spending      ~180ms      │
│  Tool 4: check_past_decisions  ~350ms      │
│  Tool 5: analyze_regrets       ~280ms      │
└─────────────────────────────────────────────┘
    ↓
Agent Synthesizes Decision
    ↓
Decision Score (1-10) + Reasoning
    ↓
PostgreSQL + Opik Cloud
```

### Tech Stack

**Backend:**
- Python 3.11+ with [uv](https://github.com/astral-sh/uv) package manager
- FastAPI web framework
- PostgreSQL 15 database
- Alembic migrations

**AI/ML:**
- [Strands](https://strands.ai) - Multi-agent orchestration
- Google Gemini 2.0 Flash - LLM reasoning
- [Opik](https://www.opik.ai) - Tracing, evaluation, PII redaction

**Authentication:**
- Google OAuth 2.0
- JWT token management

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker (for PostgreSQL)
- Google Cloud project (for OAuth + Gemini API)
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/fiscal-guard.git
cd fiscal-guard
```

2. **Install uv (if not already installed)**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fiscal_guard

# Authentication
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-secret
JWT_SECRET_KEY=your-secret-key-min-32-chars

# AI
GOOGLE_API_KEY=your-google-gemini-api-key
STRANDS_DEFAULT_MODEL=gemini-2.0-flash-exp

# Optional: Opik (for tracing)
OPIK_API_KEY=your-opik-api-key  # Optional
OPIK_WORKSPACE=default
```

4. **Start the database**
```bash
./scripts/docker-db-start.sh
```

5. **Run database migrations**
```bash
cd core
uv run alembic upgrade head
cd ..
```

6. **Start the API server**
```bash
cd api
uv run uvicorn src.api.main:app --reload --port 8000
```

7. **Open your browser**
```
http://localhost:8000/docs
```

You'll see the interactive API documentation powered by Swagger UI.

---

## 📖 Usage Examples

### 1. Authenticate

Visit the authentication endpoint to get a JWT token:
```
http://localhost:8000/auth/google/login
```

### 2. Create a Budget

```bash
curl -X POST http://localhost:8000/budgets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "total_monthly": 3000,
    "categories": {
      "groceries": {"limit": 500, "spent": 120},
      "clothing": {"limit": 200, "spent": 180},
      "entertainment": {"limit": 150, "spent": 40}
    }
  }'
```

### 3. Set Financial Goals

```bash
curl -X POST http://localhost:8000/goals \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goal_name": "Emergency Fund",
    "target_amount": 10000,
    "current_amount": 2500,
    "priority": "high",
    "deadline": "2026-12-31"
  }'
```

### 4. Get a Purchase Decision

```bash
curl -X POST http://localhost:8000/decisions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "item_name": "Designer jacket",
    "amount": 250,
    "category": "clothing",
    "reason": "Saw it on sale",
    "urgency": "low"
  }'
```

**Response:**
```json
{
  "decision_id": "uuid-here",
  "score": 3,
  "recommendation": "strong_no",
  "reasoning": "Score 3/10 (Strong No). You're at 90% of your $200 clothing budget with 12 days left in the month. This purchase would put you $230 over budget (215% over limit).\n\nGoal Impact: This delays your Emergency Fund by 2.1 weeks...",
  "alternatives": ["Wait until next month", "Set aside $50/month for 5 months"],
  "conditions": ["If it's still on sale next month", "If you get unexpected income"],
  "timestamp": "2026-01-21T10:30:00Z"
}
```

### 5. Provide Feedback

After making (or not making) the purchase:

```bash
curl -X PUT http://localhost:8000/decisions/{decision_id}/feedback \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_followed": true,
    "actually_purchased": false,
    "regret_level": 0
  }'
```

This feedback trains the AI to give you better recommendations over time!

---

## 📊 API Endpoints

### Authentication
- `GET /auth/google/login` - Initiate Google OAuth flow
- `GET /auth/google/callback` - OAuth callback
- `POST /auth/refresh` - Refresh JWT token

### Budgets
- `POST /budgets` - Create budget
- `GET /budgets` - Get all budgets
- `GET /budgets/{budget_id}` - Get specific budget
- `PUT /budgets/{budget_id}` - Update budget
- `DELETE /budgets/{budget_id}` - Delete budget
- `POST /budgets/chat-import` - Import via natural language
- `GET /budgets/current` - Get current active budget

### Goals
- `POST /goals` - Create goal
- `GET /goals` - Get all goals
- `GET /goals/{goal_id}` - Get specific goal
- `PUT /goals/{goal_id}` - Update goal
- `DELETE /goals/{goal_id}` - Delete goal
- `GET /goals/active` - Get active goals only

### Decisions
- `POST /decisions` - Get purchase decision
- `GET /decisions` - List decision history
- `GET /decisions/{decision_id}` - Get specific decision
- `PUT /decisions/{decision_id}/feedback` - Provide feedback
- `GET /decisions/stats` - Get decision statistics

### Health
- `GET /health` - Health check
- `GET /health/db` - Database health check

**Full Documentation:** http://localhost:8000/docs

---

## 🧪 Testing

### Manual Testing

Use the provided test scripts:

```bash
# Test the decision agent
python test_decision_agent.py

# Test pattern detection
python test_pattern_detection.py

# Test Strands integration
python test_strands.py
```

### Demo Scenarios

1. **Expensive discretionary purchase** (should score low)
```json
{
  "item_name": "Designer handbag",
  "amount": 800,
  "category": "clothing",
  "reason": "I like it",
  "urgency": "low"
}
```

2. **Essential purchase within budget** (should score high)
```json
{
  "item_name": "Weekly groceries",
  "amount": 75,
  "category": "groceries",
  "reason": "Need food",
  "urgency": "high"
}
```

3. **Borderline purchase** (nuanced response)
```json
{
  "item_name": "Concert ticket",
  "amount": 60,
  "category": "entertainment",
  "reason": "Friends are going",
  "urgency": "medium"
}
```

---

## 📁 Project Structure

```
fiscal-guard/
├── api/                      # FastAPI application
│   ├── src/
│   │   ├── api/             # API endpoints
│   │   ├── auth/            # Authentication
│   │   ├── services/        # Business logic
│   │   └── agents/          # AI agent implementations
│   └── pyproject.toml
├── core/                     # Core models & database
│   ├── src/
│   │   ├── models/          # SQLAlchemy models
│   │   └── database.py      # Database configuration
│   ├── alembic/             # Database migrations
│   └── pyproject.toml
├── scripts/                  # Utility scripts
│   └── docker-db-start.sh   # Database startup
├── tmp/                      # Documentation
│   ├── SETUP.md
│   ├── DECISION_AGENT.md
│   ├── OPIK_INTEGRATION.md
│   └── PROJECT_STATUS.md
├── .env.example              # Environment template
├── docker-compose.yml        # Docker configuration (future)
└── README.md                 # This file
```

---

## 🔬 Opik Integration

Fiscal Guard includes comprehensive observability with Opik:

### Automatic Tracing

Every decision request generates 7+ traces:
1. Service layer entry
2. Agent analysis
3. Budget check tool
4. Goals analysis tool
5. Spending analysis tool
6. Past decisions lookup
7. Regret pattern analysis

### PII Redaction

All sensitive data is automatically redacted:
- User UUIDs → `[UUID_REDACTED]`
- Email addresses → `[EMAIL_REDACTED]`
- Exact amounts → Rounded to nearest $10
- Sensitive fields → `[REDACTED]`

### Performance Monitoring

Track:
- Decision latency (target: <5s)
- Tool execution times
- Token usage
- Error rates
- Decision quality scores

**See full guide:** [tmp/OPIK_INTEGRATION.md](tmp/OPIK_INTEGRATION.md)

---

## 🛣️ Roadmap

### ✅ MVP Complete (Current)
- Multi-agent decision system
- 5 intelligent tools
- Pattern learning from feedback
- Opik observability
- PII redaction
- Complete API

### 🔄 Next Steps
- [ ] Comprehensive test coverage
- [ ] Demo data generation script
- [ ] Frontend web application
- [ ] Mobile app
- [ ] Bank integration (Plaid)
- [ ] RAG system with pgvector
- [ ] Predictive analytics

**See detailed roadmap:** [tmp/PROJECT_STATUS.md](tmp/PROJECT_STATUS.md)

---

## 📚 Documentation

- **[Setup Guide](tmp/SETUP.md)** - Detailed installation instructions
- **[Decision Agent API](tmp/DECISION_AGENT.md)** - Complete API reference
- **[Opik Integration](tmp/OPIK_INTEGRATION.md)** - Observability setup
- **[Project Status](tmp/PROJECT_STATUS.md)** - Current state & roadmap
- **[API Docs](http://localhost:8000/docs)** - Interactive Swagger UI

---

## 🤝 Contributing

This is currently a hackathon project. Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🏆 Acknowledgments

Built for the Strands + Opik Hackathon 2026

**Technologies:**
- [Strands](https://strands.ai) - Multi-agent orchestration framework
- [Opik](https://www.opik.ai) - LLM observability and evaluation
- [Google Gemini](https://ai.google.dev) - LLM reasoning
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

---

## 📞 Support

- **Documentation:** Check the `tmp/` directory
- **Issues:** [GitHub Issues](https://github.com/yourusername/fiscal-guard/issues)
- **API Docs:** http://localhost:8000/docs

---

**Built with ❤️ to help people make better financial decisions**

*Last Updated: January 21, 2026*
