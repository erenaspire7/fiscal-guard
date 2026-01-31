# Fiscal Guard Evaluations

LLM-powered evaluation suite for testing the Fiscal Guard conversational agent across multi-turn scenarios.

## Overview

This evaluation framework uses **LLM-as-a-Judge** metrics from Opik to validate:
- Intent classification accuracy
- State change validation
- Decision scoring quality  
- Budget math correctness
- Category classification

## Metrics

### LLM-Based Judges

#### 1. **IntentAccuracy** (LLM Judge)
Uses GPT-4o-mini to evaluate whether user messages match expected intent categories.

**What it evaluates:**
- Analyzes user messages to detect actual intent
- Compares against expected intent (log_expense, budget_query, purchase_decision, etc.)
- Provides confidence scores and reasoning

**Why LLM-based:**
The agent's internal intent classification is not returned in API responses. An LLM judge can infer intent from the user's message better than rule-based extraction.

**Example:**
```python
from evals.metrics import IntentAccuracy

metric = IntentAccuracy()
result = metric.score(output=dataset_item)
# Score: 0.95 (95% of intents correctly classified)
```

#### 2. **StateChangeAccuracy** (LLM Judge)
Uses GPT-4o to validate database state changes by analyzing conversation context and validation results.

**What it evaluates:**
- Whether expected state changes (budget updates, goal progress) occurred
- If validation failures are legitimate or false positives
- Context-aware assessment of state modifications

**Why LLM-based:**
Simple pass/fail validation misses nuance. The LLM can:
- Identify false positives in validation errors
- Understand conversation context
- Assess whether validation failures are genuine issues

**Example:**
```python
from evals.metrics import StateChangeAccuracy

metric = StateChangeAccuracy()
result = metric.score(output=dataset_item)
# Score: 0.80 (80% of state changes correctly validated)
```

### Heuristic Metrics

#### 3. **ScoreAccuracy**
Validates purchase decision scores (1-10 scale) against expected ranges.

#### 4. **DecisionCategoryAccuracy**  
Checks if purchase decisions are categorized correctly (strong_no, mild_no, mild_yes, strong_yes).

#### 5. **BudgetMathCorrectness**
Verifies budget calculations and remaining amounts in responses.

## Setup

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure API Keys

**For Gemini (default):**
```bash
export GOOGLE_API_KEY="your-google-api-key"

# Optional: Override the default model
export EVALS_LLM_MODEL="gemini/gemini-2.5-flash"
export EVALS_STATE_JUDGE_MODEL="gemini/gemini-2.5-flash"
```

**For OpenAI:**
```bash
export OPENAI_API_KEY="sk-..."
export EVALS_LLM_MODEL="gpt-4o-mini"
export EVALS_STATE_JUDGE_MODEL="gpt-4o"
```

**For Anthropic:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export EVALS_LLM_MODEL="claude-3-5-haiku-20241022"
export EVALS_STATE_JUDGE_MODEL="claude-3-5-sonnet-20241022"
```

**Programmatic override:**
```python
# Override via constructor
metric = IntentAccuracy(model="gpt-4o-mini")
metric = StateChangeAccuracy(model="ollama/llama3")
```

See [LiteLLM providers](https://docs.litellm.ai/docs/providers) for all supported models.

### 3. Configure Opik
```bash
opik configure
```

## Running Evaluations

### Run on a Single Dataset
```bash
cd evals
python -m evals.run_evaluation --dataset fiscal-guard-sarah_handlers-mt
```

### Run on All Datasets
```bash
python -m evals.run_evaluation --all
```

### Select Specific Metrics
```bash
python -m evals.run_evaluation \
  --dataset fiscal-guard-sarah_handlers-mt \
  --metrics intent_accuracy state_change_accuracy
```

### Save Results
```bash
python -m evals.run_evaluation \
  --dataset fiscal-guard-sarah_handlers-mt \
  --output results/sarah-eval.json
```

## Dataset Format

Datasets should contain multi-turn conversation scenarios:

```json
{
  "id": "...",
  "turns": [
    {
      "turn": 1,
      "input": {
        "message": "I spent $120 on groceries",
        "conversation_history": []
      },
      "expected_output": {
        "intent": "log_expense",
        "state_changes": [
          {
            "field": "budget_categories.groceries.spent",
            "operation": "+",
            "value": 120
          }
        ]
      },
      "actual_output": {
        "message": "✅ Logged $120.00...",
        "requires_clarification": false
      },
      "state_validation": {
        "valid": true,
        "checked": 1,
        "errors": []
      }
    }
  ]
}
```

## Cost Optimization

LLM-based metrics make API calls. To optimize costs:

1. **Use Gemini (default) - very cost-effective:**
   ```bash
   # Gemini 2.5 Flash: FREE up to rate limits, then ~$0.075 per 1M tokens
   export EVALS_LLM_MODEL="gemini/gemini-2.5-flash"
   ```

2. **Or use cheaper OpenAI models:**
   ```bash
   # GPT-4o-mini: ~$0.15 per 1M input tokens
   export EVALS_LLM_MODEL="gpt-4o-mini"
   ```

3. **Use local models (free but slower):**
   ```bash
   # Requires Ollama running locally
   export EVALS_LLM_MODEL="ollama/llama3"
   ```

4. **Cache results:** Opik automatically caches LLM responses for identical inputs.

5. **Sample large datasets:** Test on a subset before running full evaluations.

## Example Results

```
🔬 Running evaluation: fiscal-guard-sarah_handlers-mt
   Dataset found: 6 items
   Metrics: ['intent_accuracy', 'state_change_accuracy']

   Running evaluation...

✅ Evaluation complete!

📊 Results Summary:
   intent_accuracy: 95% (19/20 intents correctly classified)
   state_change_accuracy: 80% (12/15 state changes validated)
```

## Troubleshooting

### "AuthenticationError: Google API key not set"
Set your Gemini API key:
```bash
export GOOGLE_API_KEY="your-google-api-key"
```

Get a free key at: https://aistudio.google.com/apikey

### "AuthenticationError: OpenAI API key not set"
If using OpenAI instead of Gemini:
```bash
export OPENAI_API_KEY="sk-..."
export EVALS_LLM_MODEL="gpt-4o-mini"
```

### "No module named evals"
Run from the evals directory:
```bash
cd evals
python -m evals.run_evaluation --help
```

### High LLM costs
Switch to free Gemini or local models:
```bash
export EVALS_LLM_MODEL="gemini/gemini-2.5-flash"  # Free tier available
# or
export EVALS_LLM_MODEL="ollama/llama3"  # Completely free, local
```

## Architecture

```
evals/
├── src/evals/
│   ├── metrics/
│   │   ├── intent_accuracy.py          # LLM judge for intent
│   │   ├── state_change_accuracy.py    # LLM judge for state
│   │   ├── score_accuracy.py           # Heuristic
│   │   ├── decision_category_accuracy.py
│   │   └── budget_math_correctness.py
│   ├── run_evaluation.py               # Main CLI
│   └── datasets/
│       └── generator.py                # Dataset creation
├── test_metrics.py                     # Quick metric tests
└── README.md                           # This file
```

## References

- [Opik LLM-as-a-Judge Documentation](https://www.comet.com/docs/opik/evaluation/metrics/overview#llm-as-a-judge-metrics)
- [Multi-turn Conversation Metrics](https://www.comet.com/docs/opik/evaluation/metrics/overview#multi-turn-conversation-evaluation)
- [Custom Metrics Guide](https://www.comet.com/docs/opik/evaluation/metrics/custom_metric)
