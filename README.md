# Fiscal Guard

**Your AI Financial Companion - Prevent Buyer's Remorse Before It Happens**

[![Status](https://img.shields.io/badge/status-MVP_Complete-success)](https://github.com/erenaspire7/fiscal-guard)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org)
[![React](https://img.shields.io/badge/react-19+-61DAFB)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🎯 What is Fiscal Guard?

Fiscal Guard is an AI-powered financial decision assistant that helps you make smarter purchasing decisions by analyzing your budget, goals, and spending patterns **before** you buy.

Unlike traditional budgeting apps that show you what you overspent *after the fact*, Fiscal Guard intervenes at the moment of decision with personalized insights powered by a **Multi-Agent System** (Strands + Gemini 2.0) and **Real-Time Observability** (Opik).

### The Problem

Americans spend an average of **$21,000/year** on impulse purchases they later regret. Traditional budgeting tools are passive—they tell you the bad news after the money is gone.

### Our Solution

**Active intervention:** Chat with AI before making a purchase. The agent adopts a persona (e.g., "Financial Monk") to guide you based on your strictness settings, checking your budget, goals, and emotional history in real-time.

---

## ✨ Key Features

### 🛡️ Shield (Agent Chat)
Direct chat interface for real-time purchase analysis.
- **5-Tool Analysis**: Checks Budget, Goals, Financial Health, Past Decisions, and Regret Patterns.
- **Persona Adaptation**: Choose from **Gentle**, **Balanced**, or **Financial Monk** personas.
- **Responsive UI**: Fully optimized for both Desktop and Mobile experiences.

### 📊 Command (Dashboard)
Real-time discipline hub.
- **Guard Score**: A dynamic score (0-100) reflecting your recent financial discipline.
- **Growth Analysis**: Rich trend graph showing your decision quality over time with "Danger Zone" indicators.
- **Budget Health**: Visual indicators for category utilization.

### 🧠 Insights (Regret Tracker)
Close the loop on your decisions.
- **Feedback Loop**: Rate your satisfaction with past purchases to train the AI.
- **Pattern Recognition**: The system learns triggers (e.g., *"You often regret clothing purchases over $100"*).
- **Peace of Mind Score**: Tracks your impulse control growth.

### 🏦 Vault (Budgets & Goals)
Asset security management.
- **Goal Progress**: Contribute to goals directly from the UI with an interactive modal.
- **Smart Budgets**: Category-based tracking with visual progress bars.

### 🔒 Enterprise-Grade Security & Observability
- **Dual Auth**: Login with Google OAuth or Email/Password (Bcrypt).
- **Opik Tracing**: Full visibility into agent reasoning with automatic PII redaction.
- **Privacy First**: User IDs, emails, and exact amounts are redacted in traces.

---

## 🏗️ Architecture

The system uses a modern decoupled architecture:

```
[React 19 Frontend]
    ↓ (REST API)
[FastAPI Backend]
    ↓ (Auth via JWT)
[Decision Service]
    ↓ (Opik Tracing)
[Decision Agent (Strands + Gemini 2.0 Flash)]
    ↓ ⟷ [Tools: check_budget, check_goals, analyze_history, analyze_regret]
[PostgreSQL Database]
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ & Node.js 18+
- Docker (for PostgreSQL)
- Google Cloud API Key (Gemini)

### 1. Setup & Install
```bash
# Clone repo
git clone https://github.com/yourusername/fiscal-guard.git
cd fiscal-guard

# Setup environment
cp .env.example .env
# Edit .env with your keys (DATABASE_URL, GOOGLE_API_KEY, etc.)
```

### 2. Start Database & Backend
```bash
# Start DB
./scripts/docker-db-start.sh

# Run Migrations & Seed Demo Data
cd core
uv run alembic upgrade head
uv run python -m core.scripts.seed_demo_data

# Start API
cd ../api
uv run uvicorn src.api.main:app --reload --port 8000
```

### 3. Start Frontend
```bash
cd ../ui
npm install
npm run dev
```

Visit **http://localhost:5173** to launch the application.

---

## 👤 Demo Accounts

We have pre-seeded 3 distinct user personas for testing:

| User | Email | Password | Persona | Focus |
|------|-------|----------|---------|-------|
| **Sarah Chen** | `demo+sarah@fiscalguard.app` | `demo123` | **Financial Monk** | Impulsive shopping correction |
| **Alex Sterling** | `demo+alex@fiscalguard.app` | `demo123` | **Balanced** | Healthy habits maintenance |
| **Marcus Wu** | `demo+marcus@fiscalguard.app` | `demo123` | **Gentle** | Extreme frugality support |

---

## 🧪 Demo Scenarios

### Scenario A: Sarah's Shopping Addiction
1. **Login** as Sarah (Financial Monk).
2. **Dashboard**: Note the "At Risk" status and recent low scores.
3. **Chat**: Ask *"I want to buy $450 designer boots."*
4. **Result**: The agent will strongly deny based on her history of regretting luxury fashion purchases, citing her budget limits.

### Scenario B: Alex's Balanced Lifestyle
1. **Login** as Alex (Balanced).
2. **Chat**: Ask *"Can I buy concert tickets for $150?"*
3. **Result**: Agent checks the "Vacation Fund" goal. It approves but suggests adding $50 to the goal to stay on track.
4. **Vault**: Go to Vault and add the contribution to show progress.

### Scenario C: Marcus's Investment Focus
1. **Login** as Marcus (Gentle).
2. **Insights**: Review high Guard Score and capital retained.
3. **Chat**: Ask *"Should I buy this $300 investment course?"*
4. **Result**: Agent encourages the purchase as it aligns with his long-term wealth goals.

---

## 📁 Project Structure

```
fiscal-guard/
├── api/              # FastAPI Backend Application
├── core/             # Database Models, Migrations & Business Logic
├── ui/               # React + Tailwind + Shadcn UI Frontend
├── scripts/          # Utility scripts (Docker, Seeding)
└── tmp/              # Documentation & Status Tracking
```

---

## 🏆 Tech Stack

- **Frontend**: React 19, TailwindCSS, Radix UI, Recharts, Framer Motion
- **Backend**: FastAPI, Python 3.11, Pydantic
- **AI**: Strands (Orchestration), Google Gemini 2.0 Flash (Reasoning)
- **Observability**: Opik (Comet.ml) for Tracing & Evaluation
- **Database**: PostgreSQL, SQLAlchemy, Alembic

---

## 📄 License

MIT License. Built for the Strands + Opik Hackathon 2026.