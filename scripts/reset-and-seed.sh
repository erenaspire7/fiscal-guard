#!/bin/bash
# Reset database and seed with demo data for Fiscal Guard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse flags
SKIP_RESET=false
SKIP_SEED=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-reset)
            SKIP_RESET=true
            shift
            ;;
        --skip-seed)
            SKIP_SEED=true
            shift
            ;;
        --help)
            echo "Usage: ./scripts/reset-and-seed.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-reset    Skip database reset (only run seed)"
            echo "  --skip-seed     Skip seeding (only reset database)"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./scripts/reset-and-seed.sh                  # Reset and seed"
            echo "  ./scripts/reset-and-seed.sh --skip-reset     # Only seed"
            echo "  ./scripts/reset-and-seed.sh --skip-seed      # Only reset"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🔄 Fiscal Guard - Database Reset & Seed${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}📝 Please edit .env with your credentials before running again${NC}"
    exit 1
fi

# Export environment variables from .env file
echo -e "${BLUE}📦 Loading environment variables...${NC}"
set -a
source .env
set +a

# Check for required GOOGLE_API_KEY
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your-google-api-key" ]; then
    echo -e "${RED}❌ GOOGLE_API_KEY is required${NC}"
    echo "   Please set it in your .env file"
    echo "   Get your key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Check if database is accessible
echo -e "${BLUE}🔍 Checking database connection...${NC}"
cd core
DB_CHECK=$(python -c "
import os
from sqlalchemy import create_engine, text
try:
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('success')
except Exception as e:
    print(f'error: {e}')
" 2>&1)
cd ..

if [[ $DB_CHECK != "success" ]]; then
    echo -e "${RED}❌ Cannot connect to database${NC}"
    echo "   DATABASE_URL: $DATABASE_URL"
    echo "   Error: $DB_CHECK"
    echo ""
    echo "Make sure PostgreSQL is running:"
    echo "  - macOS: brew services start postgresql"
    echo "  - Linux: sudo systemctl start postgresql"
    echo "  - Docker/OrbStack: Check if containers are running"
    exit 1
fi
echo -e "${GREEN}✅ Database connection successful${NC}"
echo ""

# Reset database if not skipped
if [ "$SKIP_RESET" = false ]; then
    echo -e "${YELLOW}🗑️  Resetting database...${NC}"
    echo -e "${YELLOW}⚠️  This will DELETE ALL DATA!${NC}"

    # Prompt for confirmation
    read -p "Are you sure you want to continue? (yes/no): " confirmation
    if [ "$confirmation" != "yes" ]; then
        echo -e "${BLUE}ℹ️  Reset cancelled${NC}"
        exit 0
    fi

    cd core

    # Drop all tables by downgrading to base
    echo -e "${BLUE}   Dropping all tables...${NC}"
    uv run alembic downgrade base

    # Run migrations from scratch
    echo -e "${BLUE}   Running migrations from scratch...${NC}"
    uv run alembic upgrade head

    cd ..
    echo -e "${GREEN}✅ Database reset complete${NC}"
    echo ""
else
    echo -e "${BLUE}ℹ️  Skipping database reset${NC}"
    echo ""
fi

# Seed database if not skipped
if [ "$SKIP_SEED" = false ]; then
    echo -e "${BLUE}🌱 Seeding database with demo data...${NC}"
    echo -e "${BLUE}   (Using direct database insertion - no API required)${NC}"
    echo ""

    # Run seed script (Python-based, bypasses API for speed)
    echo -e "${BLUE}📊 Creating demo users and data...${NC}"

    uv run python -m evals.utils.seed_data
    SEED_EXIT_CODE=$?

    if [ $SEED_EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✨ Database seeded successfully!${NC}"
        echo ""
        echo -e "${BLUE}📝 Demo Accounts Created:${NC}"
        echo ""
        echo -e "${GREEN}Sarah Chen (Impulsive → Improving)${NC}"
        echo "  Email: demo+sarah@fiscalguard.app"
        echo "  Password: demo123"
        echo "  Persona: Financial Monk (9/10 strictness)"
        echo "  Budget: Resets on 1st of month"
        echo "  Pattern: 36 decisions over 6 months, improving trend"
        echo ""
        echo -e "${GREEN}Alex Sterling (Balanced)${NC}"
        echo "  Email: demo+alex@fiscalguard.app"
        echo "  Password: demo123"
        echo "  Persona: Balanced (5/10 strictness)"
        echo "  Budget: Resets on 15th of month"
        echo "  Pattern: 24 decisions over 6 months, stable performance"
        echo ""
        echo -e "${GREEN}Marcus Wu (Financial Monk)${NC}"
        echo "  Email: demo+marcus@fiscalguard.app"
        echo "  Password: demo123"
        echo "  Persona: Gentle (2/10 strictness)"
        echo "  Budget: Resets on 25th of month"
        echo "  Pattern: 18 decisions over 6 months, highly disciplined"
        echo ""
        echo -e "${BLUE}🚀 Ready to start the application:${NC}"
        echo "  API: cd api && uv run uvicorn src.api.main:app --reload"
        echo "  UI:  cd ui && yarn dev"
        echo ""
    else
        echo ""
        echo -e "${RED}❌ Seeding failed (exit code: $SEED_EXIT_CODE)${NC}"
        exit $SEED_EXIT_CODE
    fi
else
    echo -e "${BLUE}ℹ️  Skipping database seed${NC}"
    echo ""
fi

echo -e "${GREEN}✅ All done!${NC}"
