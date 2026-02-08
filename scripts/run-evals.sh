#!/bin/bash
# Run evaluations for Fiscal Guard

set -e

# Parse flags
RESET_DB=false
EVAL_SCENARIO=""
KEEP_ALIVE=false
MODE="all"  # all, single-turn, multi-turn, eval-only
SKIP_GENERATION=false
SKIP_EVALUATION=false
MAX_CONCURRENT=5  # Default concurrent requests

while [[ $# -gt 0 ]]; do
    case $1 in
        --reset-db)
            RESET_DB=true
            shift
            ;;
        --keep-alive)
            KEEP_ALIVE=true
            shift
            ;;
        --skip-generation)
            SKIP_GENERATION=true
            shift
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --single-turn)
            MODE="single-turn"
            shift
            ;;
        --multi-turn)
            MODE="multi-turn"
            shift
            ;;
        --eval-only)
            MODE="eval-only"
            shift
            ;;
        --generate-only)
            SKIP_EVALUATION=true
            shift
            ;;
        --max-concurrent)
            MAX_CONCURRENT="$2"
            shift 2
            ;;
        *)
            EVAL_SCENARIO="$1"
            shift
            ;;
    esac
done

# Track PIDs for cleanup
API_PID=""

# Cleanup function
cleanup() {
    if [ "$KEEP_ALIVE" = true ]; then
        echo ""
        echo "🔄 Keeping API running (--keep-alive enabled)"
        echo "   API PID: $API_PID"
        echo "   Stop manually with: kill $API_PID"
        return
    fi

    echo ""
    echo "🛑 Shutting down services..."

    if [ -n "$API_PID" ]; then
        echo "Stopping API (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
    fi

    echo "✅ Cleanup complete"
}

# Set up trap to catch Ctrl+C (SIGINT) and other termination signals
trap cleanup SIGINT SIGTERM EXIT

echo "🧪 Starting Evaluation Environment..."
echo "   Mode: $MODE"
echo "   Max concurrent requests: $MAX_CONCURRENT"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your credentials before running again"
    exit 1
fi

# Export environment variables from .env file
echo "📦 Loading environment variables..."
set -a
source .env
set +a

# Check for required GOOGLE_API_KEY
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your-google-api-key" ]; then
    echo "❌ GOOGLE_API_KEY is required for evaluations"
    echo "   Please set it in your .env file"
    echo "   Get your key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Enable internal endpoints for evaluation
export ALLOW_INTERNAL_ENDPOINTS=true

# Set internal API token if not already set
if [ -z "$INTERNAL_API_TOKEN" ]; then
    export INTERNAL_API_TOKEN="eval-token-$(date +%s)"
    echo "⚙️  Generated internal API token: $INTERNAL_API_TOKEN"
fi

# Skip API startup for eval-only mode
if [ "$MODE" != "eval-only" ]; then
    # Reset database if requested
    if [ "$RESET_DB" = true ]; then
        echo "🗑️  Resetting database..."
        cd core

        # Drop all tables by downgrading to base
        echo "   Dropping all tables..."
        uv run alembic downgrade base

        # Run migrations from scratch
        echo "   Running migrations from scratch..."
        uv run alembic upgrade head

        # Seed demo data
        echo "   Seeding demo data..."
        cd ../evals
        uv run python -m evals.utils.seed_data
        cd ..

        echo "✅ Database reset and seeded"
    else
        # Run migrations normally
        echo "🔄 Running database migrations..."
        cd core
        uv run migrate
        cd ..

        # Check if we need to seed data
        echo "⚙️  Ensuring demo data is seeded..."
        cd evals
        uv run python -m evals.utils.seed_data
        cd ..
    fi

    # Start API in background with log file
    echo "🚀 Starting API server..."
    API_LOG_FILE="api_eval.log"
    cd api
    uv run uvicorn src.api.main:app --port 8000 > "../${API_LOG_FILE}" 2>&1 &
    API_PID=$!
    echo "   API started with PID: $API_PID"
    echo "   API logs: ${API_LOG_FILE}"
    cd ..

    # Wait for API to be ready
    echo "⏳ Waiting for API to be ready..."
    sleep 3

    # Health check for API
    MAX_RETRIES=30
    RETRY_COUNT=0
    echo "🔍 Checking API health..."
    while ! curl -s http://localhost:8000/health > /dev/null; do
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
            echo "❌ API failed to start after ${MAX_RETRIES} attempts"
            exit 1
        fi
        echo "   Waiting for API... (${RETRY_COUNT}/${MAX_RETRIES})"
        sleep 1
    done
    echo "✅ API is ready"
fi

# Run evaluations
echo ""
echo "🎬 Running evaluations..."
cd evals

EVAL_EXIT_CODE=0

# Function to run single-turn scenarios
run_single_turn() {
    local scenario=$1

    if [ -n "$scenario" ]; then
        # Check if scenario file exists
        if [ ! -f "src/evals/scenarios/purchase_decisions/${scenario}.json" ]; then
            echo "⚠️  Single-turn scenario not found: ${scenario}"
            return 0
        fi

        echo ""
        echo "📊 Single-turn scenario: $scenario"

        # Generate dataset (unless skipped)
        if [ "$SKIP_GENERATION" = false ]; then
            echo "   Step 1: Generating dataset..."
            uv run python -m evals.datasets.generator \
                --scenario "src/evals/scenarios/purchase_decisions/${scenario}.json" \
                --api-url http://localhost:8000 \
                --max-concurrent "$MAX_CONCURRENT"
        else
            echo "   Step 1: Skipping dataset generation (using existing data)"
        fi

        # Run evaluation (unless skipped)
        if [ "$SKIP_EVALUATION" = false ]; then
            echo "   Step 2: Running evaluation..."
            uv run python -m evals.run_evaluation \
                --dataset "fiscal-guard-${scenario}"
        else
            echo "   Step 2: Skipping evaluation (generate-only mode)"
        fi
    else
        # Run all single-turn scenarios
        for scenario_file in src/evals/scenarios/purchase_decisions/*.json; do
            if [ -f "$scenario_file" ]; then
                scenario_name=$(basename "$scenario_file" .json)
                echo ""
                echo "📊 Single-turn scenario: $scenario_name"

                # Generate dataset (unless skipped)
                if [ "$SKIP_GENERATION" = false ]; then
                    echo "   Step 1: Generating dataset..."
                    uv run python -m evals.datasets.generator \
                        --scenario "$scenario_file" \
                        --api-url http://localhost:8000 \
                        --max-concurrent "$MAX_CONCURRENT"
                else
                    echo "   Step 1: Skipping dataset generation (using existing data)"
                fi

                # Run evaluation (unless skipped)
                if [ "$SKIP_EVALUATION" = false ]; then
                    echo "   Step 2: Running evaluation..."
                    uv run python -m evals.run_evaluation \
                        --dataset "fiscal-guard-${scenario_name}"
                else
                    echo "   Step 2: Skipping evaluation (generate-only mode)"
                fi
            fi
        done
    fi
}

# Function to run multi-turn scenarios
run_multi_turn() {
    local scenario=$1

    if [ -n "$scenario" ]; then
        # Check if scenario file exists
        if [ ! -f "src/evals/scenarios/multi_turn/${scenario}.json" ]; then
            echo "⚠️  Multi-turn scenario not found: ${scenario}"
            return 0
        fi

        echo ""
        echo "🔄 Multi-turn scenario: $scenario"

        # Generate dataset (unless skipped)
        if [ "$SKIP_GENERATION" = false ]; then
            echo "   Step 1: Generating dataset..."
            uv run python -m evals.datasets.multi_turn_generator \
                --scenario "src/evals/scenarios/multi_turn/${scenario}.json" \
                --api-url http://localhost:8000 \
                --internal-token "$INTERNAL_API_TOKEN" \
                --max-concurrent "$MAX_CONCURRENT"
        else
            echo "   Step 1: Skipping dataset generation (using existing data)"
        fi

        # Run evaluation (unless skipped)
        if [ "$SKIP_EVALUATION" = false ]; then
            echo "   Step 2: Running evaluation..."
            uv run python -m evals.run_evaluation \
                --dataset "fiscal-guard-${scenario}-mt" \
                --metrics state_change_accuracy
        else
            echo "   Step 2: Skipping evaluation (generate-only mode)"
        fi
    else
        # Run all multi-turn scenarios
        for scenario_file in src/evals/scenarios/multi_turn/*.json; do
            if [ -f "$scenario_file" ]; then
                scenario_name=$(basename "$scenario_file" .json)
                echo ""
                echo "🔄 Multi-turn scenario: $scenario_name"

                # Generate dataset (unless skipped)
                if [ "$SKIP_GENERATION" = false ]; then
                    echo "   Step 1: Generating dataset..."
                    uv run python -m evals.datasets.multi_turn_generator \
                        --scenario "$scenario_file" \
                        --api-url http://localhost:8000 \
                        --internal-token "$INTERNAL_API_TOKEN" \
                        --max-concurrent "$MAX_CONCURRENT"
                else
                    echo "   Step 1: Skipping dataset generation (using existing data)"
                fi

                # Run evaluation (unless skipped)
                if [ "$SKIP_EVALUATION" = false ]; then
                    echo "   Step 2: Running evaluation..."
                    uv run python -m evals.run_evaluation \
                        --dataset "fiscal-guard-${scenario_name}-mt" \
                        --metrics state_change_accuracy
                else
                    echo "   Step 2: Skipping evaluation (generate-only mode)"
                fi
            fi
        done
    fi
}

# Function to run evaluations only (no dataset generation)
run_eval_only() {
    echo ""
    echo "🔬 Running evaluations only (no dataset generation)..."

    if [ -n "$EVAL_SCENARIO" ]; then
        echo "   Evaluating dataset: fiscal-guard-${EVAL_SCENARIO}"
        uv run python -m evals.run_evaluation \
            --dataset "fiscal-guard-${EVAL_SCENARIO}"
    else
        echo "   Evaluating all datasets..."
        uv run python -m evals.run_evaluation --all
    fi
}

# Execute based on mode
case "$MODE" in
    single-turn)
        run_single_turn "$EVAL_SCENARIO"
        ;;
    multi-turn)
        run_multi_turn "$EVAL_SCENARIO"
        ;;
    eval-only)
        run_eval_only
        ;;
    all)
        # Run both single-turn and multi-turn
        echo "🎯 Running all evaluation types..."
        run_single_turn "$EVAL_SCENARIO"
        run_multi_turn "$EVAL_SCENARIO"
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        echo "   Valid modes: all, single-turn, multi-turn, eval-only"
        exit 1
        ;;
esac

EVAL_EXIT_CODE=$?

cd ..

echo ""
if [ $EVAL_EXIT_CODE -eq 0 ]; then
    echo "✅ All evaluations completed!"
else
    echo "❌ Some evaluations failed (exit code: $EVAL_EXIT_CODE)"
fi

# Show API log location if API was started
if [ "$MODE" != "eval-only" ] && [ -f "api_eval.log" ]; then
    echo ""
    echo "📋 API logs available at: api_eval.log"
    echo "   View with: tail -f api_eval.log"
    echo "   Search errors: grep -i error api_eval.log"

    # Show dataset generation summary if evaluation was skipped
    if [ "$SKIP_EVALUATION" = true ]; then
        echo ""
        echo "💡 Datasets generated! Run evaluation with:"
        echo "   ./scripts/run-evals.sh --eval-only"
    fi
fi

# Print usage summary
echo ""
echo "📚 Usage examples:"
echo "   All scenarios:           ./scripts/run-evals.sh"
echo "   Single-turn only:        ./scripts/run-evals.sh --single-turn"
echo "   Multi-turn only:         ./scripts/run-evals.sh --multi-turn"
echo "   Specific scenario:       ./scripts/run-evals.sh --multi-turn sarah_handlers"
echo "   Generate datasets only:  ./scripts/run-evals.sh --generate-only --multi-turn"
echo "   Eval existing datasets:  ./scripts/run-evals.sh --eval-only"
echo "   Skip dataset generation: ./scripts/run-evals.sh --skip-generation"
echo "   Keep API running:        ./scripts/run-evals.sh --keep-alive"
echo "   Reset DB first:          ./scripts/run-evals.sh --reset-db"
echo "   Custom concurrency:      ./scripts/run-evals.sh --max-concurrent 10"
echo "   Debug (sequential):      ./scripts/run-evals.sh --max-concurrent 1"

if [ "$KEEP_ALIVE" = false ]; then
    exit $EVAL_EXIT_CODE
fi
