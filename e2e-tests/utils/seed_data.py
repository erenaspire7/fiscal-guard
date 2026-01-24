"""
Seed demo data directly into the database.

This script bypasses the API endpoints and directly inserts records,
avoiding AI agent evaluation delays during seeding.
"""

import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

# Add core to path (go up two levels from e2e-tests-v2/utils to project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core" / "src"))

# Load environment variables from .env file BEFORE importing config
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
if not env_path.exists():
    raise FileNotFoundError(f".env file not found at {env_path}")
load_dotenv(env_path, override=True)

from core.database.models import Base, Budget, BudgetItem, Goal, PurchaseDecision, User
from core.services.auth import AuthService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Get DATABASE_URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_budget_period(year: int, month: int, reset_day: int) -> tuple[date, date]:
    """Get budget period dates based on reset day."""
    from calendar import monthrange

    if reset_day == 1:
        start = date(year, month, 1)
        # Get last day of month
        _, last_day = monthrange(year, month)
        end = date(year, month, last_day)
        return start, end

    # Custom reset day
    start = date(year, month, reset_day)
    if month == 12:
        end = date(year + 1, 1, reset_day - 1)
    else:
        end = date(year, month + 1, reset_day - 1)
    return start, end


def create_user(
    db,
    email: str,
    password: str,
    full_name: str,
    persona_tone: str,
    strictness_level: int,
) -> User:
    """Create or get existing user."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"  ✓ User {email} already exists")
        return existing

    auth_service = AuthService(db)
    password_hash = auth_service.hash_password(password)

    user = User(
        user_id=uuid4(),
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        persona_tone=persona_tone,
        strictness_level=strictness_level,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"  ✓ Created user {email}")
    return user


def create_budget(
    db,
    user_id: UUID,
    name: str,
    total_monthly: Decimal,
    period_start: date,
    period_end: date,
    categories: dict,
) -> Budget:
    """Create or get existing budget."""
    existing = (
        db.query(Budget).filter(Budget.user_id == user_id, Budget.name == name).first()
    )
    if existing:
        print(f"    ⏭️  Budget '{name}' already exists")
        return existing

    budget = Budget(
        budget_id=uuid4(),
        user_id=user_id,
        name=name,
        total_monthly=total_monthly,
        period_start=period_start,
        period_end=period_end,
        categories=categories,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def create_goal(
    db,
    user_id: UUID,
    goal_name: str,
    target_amount: Decimal,
    current_amount: Decimal,
    priority: str,
    deadline: date,
) -> Goal:
    """Create or get existing goal."""
    existing = (
        db.query(Goal)
        .filter(Goal.user_id == user_id, Goal.goal_name == goal_name)
        .first()
    )
    if existing:
        print(f"    ⏭️  Goal '{goal_name}' already exists")
        return existing

    goal = Goal(
        goal_id=uuid4(),
        user_id=user_id,
        goal_name=goal_name,
        target_amount=target_amount,
        current_amount=current_amount,
        priority=priority,
        deadline=deadline,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def create_budget_item(
    db,
    budget_id: UUID,
    user_id: UUID,
    item_name: str,
    amount: Decimal,
    category: str,
    transaction_date: datetime,
    decision_id: UUID | None = None,
    notes: str | None = None,
    is_planned: bool = False,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> BudgetItem:
    """Create a budget item to track spending against budget."""
    budget_item = BudgetItem(
        item_id=uuid4(),
        budget_id=budget_id,
        user_id=user_id,
        item_name=item_name,
        amount=amount,
        category=category,
        transaction_date=transaction_date,
        decision_id=decision_id,
        notes=notes,
        is_planned=is_planned,
        created_at=created_at or datetime.utcnow(),
        updated_at=updated_at or datetime.utcnow(),
    )
    db.add(budget_item)
    db.commit()
    db.refresh(budget_item)

    # Update budget's spent amount for this category
    budget = db.query(Budget).filter(Budget.budget_id == budget_id).first()
    if budget and category in budget.categories:
        # Create a new dict to trigger SQLAlchemy's change detection for JSONB
        categories_copy = dict(budget.categories)
        categories_copy[category]["spent"] = float(
            categories_copy[category].get("spent", 0)
        ) + float(amount)
        budget.categories = categories_copy

        # Mark the column as modified to ensure SQLAlchemy detects the change
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(budget, "categories")

        db.commit()

    return budget_item


def create_decision(
    db,
    user_id: UUID,
    item_name: str,
    amount: Decimal,
    category: str,
    reason: str,
    urgency: str,
    score: int,
    decision_category: str,
    reasoning: str,
    analysis: dict,
    alternatives: list[str] | None = None,
    conditions: list[str] | None = None,
    actual_purchase: bool | None = None,
    regret_level: int | None = None,
    user_feedback: str | None = None,
    budget_id: UUID | None = None,
    transaction_date: datetime | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> PurchaseDecision:
    """Create a purchase decision directly without AI evaluation."""
    existing = (
        db.query(PurchaseDecision)
        .filter(
            PurchaseDecision.user_id == user_id,
            PurchaseDecision.item_name == item_name,
            PurchaseDecision.amount == amount,
        )
        .first()
    )
    if existing:
        print(f"    ⏭️  Decision '{item_name}' already exists")
        return existing

    decision = PurchaseDecision(
        decision_id=uuid4(),
        user_id=user_id,
        item_name=item_name,
        amount=amount,
        category=category,
        reason=reason,
        urgency=urgency,
        score=score,
        decision_category=decision_category,
        reasoning=reasoning,
        analysis=analysis,
        alternatives=alternatives,
        conditions=conditions,
        actual_purchase=actual_purchase,
        regret_level=regret_level,
        user_feedback=user_feedback,
        created_at=created_at or datetime.utcnow(),
        updated_at=updated_at or datetime.utcnow(),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    # If purchase was actually made, create a budget item to track it
    if actual_purchase and budget_id:
        create_budget_item(
            db=db,
            budget_id=budget_id,
            user_id=user_id,
            item_name=item_name,
            amount=amount,
            category=category,
            transaction_date=transaction_date or datetime.utcnow(),
            decision_id=decision.decision_id,
            notes=f"Score: {score}/10 - {decision_category}",
            is_planned=False,
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
        )

    return decision


def seed_sarah(db, user: User):
    """Seed Sarah's data - Impulsive buyer improving over time."""
    print("  📊 Creating 6 months of budgets and decisions...")

    months = []
    today = datetime.utcnow()
    for i in range(5, -1, -1):
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m, datetime(y, m, 1).strftime("%B %Y")))

    base_categories = {
        "groceries": {"limit": 600, "spent": 0},
        "dining": {"limit": 200, "spent": 0},
        "shopping": {"limit": 300, "spent": 0},
        "entertainment": {"limit": 150, "spent": 0},
        "transport": {"limit": 400, "spent": 0},
    }

    # Sarah's purchase patterns per month
    purchase_patterns = [
        # Month 1: Heavy overspending
        [
            {
                "item_name": "Designer Dress",
                "amount": Decimal("450"),
                "category": "shopping",
                "reason": "Saw it on Instagram",
                "urgency": "low",
                "score": 2,
                "decision_category": "strong_no",
                "reasoning": "This is a high-cost impulse purchase driven by social media influence. Your shopping budget is $300, and this single item would consume 150% of it. This directly conflicts with your emergency fund goal.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 0,
                        "limit": 300,
                        "remaining": 300,
                        "percentage_used": 0,
                        "would_exceed": True,
                        "impact_description": "This purchase would exceed your shopping budget by $150",
                    },
                    "affected_goals": [],
                    "purchase_category": "impulse",
                    "financial_health_score": 45,
                },
                "alternatives": [
                    "Wait 30 days to see if you still want it",
                    "Look for similar styles at more affordable retailers",
                    "Set this as a reward for achieving a savings milestone",
                ],
                "conditions": [
                    "You have extra income this month beyond your budget",
                    "You've already met your monthly savings goal",
                ],
                "actual_purchase": True,
                "regret_level": 9,
                "user_feedback": "Wore it once, total waste",
            },
            {
                "item_name": "Luxury Dinner",
                "amount": Decimal("180"),
                "category": "dining",
                "reason": "Celebrating nothing special",
                "urgency": "low",
                "score": 3,
                "decision_category": "strong_no",
                "reasoning": "While celebrating is important, a $180 dinner without a special occasion is excessive. This represents 90% of your $200 monthly dining budget.",
                "analysis": {
                    "budget_analysis": {
                        "category": "dining",
                        "current_spent": 0,
                        "limit": 200,
                        "remaining": 200,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "This would use 90% of your dining budget in one meal",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 45,
                },
                "alternatives": [
                    "Choose a restaurant with $60-80 pricing",
                    "Cook a special meal at home",
                ],
                "actual_purchase": True,
                "regret_level": 7,
                "user_feedback": "Food was good but too expensive",
            },
            {
                "item_name": "Designer Shoes",
                "amount": Decimal("280"),
                "category": "shopping",
                "reason": "Limited edition",
                "urgency": "high",
                "score": 2,
                "decision_category": "strong_no",
                "reasoning": "Another luxury shopping item. Combined with the dress, you'd be $430 over your shopping budget. 'Limited edition' creates false urgency for non-essential items.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 450,
                        "limit": 300,
                        "remaining": -150,
                        "percentage_used": 150,
                        "would_exceed": True,
                        "impact_description": "Already $150 over budget, this adds another $280",
                    },
                    "affected_goals": [],
                    "purchase_category": "impulse",
                    "financial_health_score": 35,
                },
                "actual_purchase": True,
                "regret_level": 8,
                "user_feedback": "Uncomfortable and overpriced",
            },
            {
                "item_name": "Concert VIP Tickets",
                "amount": Decimal("250"),
                "category": "entertainment",
                "reason": "FOMO",
                "urgency": "medium",
                "score": 4,
                "decision_category": "mild_no",
                "reasoning": "VIP tickets are 167% of your entertainment budget. Regular tickets would provide the same experience for less. FOMO is not a sound financial reason.",
                "analysis": {
                    "budget_analysis": {
                        "category": "entertainment",
                        "current_spent": 0,
                        "limit": 150,
                        "remaining": 150,
                        "percentage_used": 0,
                        "would_exceed": True,
                        "impact_description": "This exceeds entertainment budget by $100",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 35,
                },
                "alternatives": [
                    "Buy regular tickets instead",
                    "Find a friend to split VIP package",
                ],
                "actual_purchase": True,
                "regret_level": 5,
                "user_feedback": "Fun but not worth the price",
            },
            {
                "item_name": "Uber Rides",
                "amount": Decimal("120"),
                "category": "transport",
                "reason": "Too lazy to drive",
                "urgency": "low",
                "score": 3,
                "decision_category": "strong_no",
                "reasoning": "Convenience spending due to laziness. At $120, you're spending 30% of your transport budget on avoidable costs.",
                "analysis": {
                    "budget_analysis": {
                        "category": "transport",
                        "current_spent": 0,
                        "limit": 400,
                        "remaining": 400,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 30% of transport budget unnecessarily",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 30,
                },
                "alternatives": [
                    "Drive yourself",
                    "Use public transportation",
                    "Plan trips better to consolidate errands",
                ],
                "actual_purchase": True,
                "regret_level": 6,
                "user_feedback": "Should have driven",
            },
            {
                "item_name": "Takeout Food",
                "amount": Decimal("80"),
                "category": "dining",
                "reason": "Too tired to cook",
                "urgency": "low",
                "score": 5,
                "decision_category": "mild_no",
                "reasoning": "Combined with the luxury dinner, you're now at $260 dining spending ($60 over budget). Meal prepping on weekends would solve this.",
                "analysis": {
                    "budget_analysis": {
                        "category": "dining",
                        "current_spent": 180,
                        "limit": 200,
                        "remaining": 20,
                        "percentage_used": 90,
                        "would_exceed": True,
                        "impact_description": "This pushes dining $60 over budget",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 30,
                },
                "actual_purchase": True,
                "regret_level": 4,
                "user_feedback": "Convenience was nice",
            },
        ],
        # Month 2: Still overspending but slightly better
        [
            {
                "item_name": "New Handbag",
                "amount": Decimal("380"),
                "category": "shopping",
                "reason": "Matching my new shoes",
                "urgency": "low",
                "score": 2,
                "decision_category": "strong_no",
                "reasoning": "Trying to justify a purchase based on a previous poor decision. This is $80 over your entire shopping budget.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 0,
                        "limit": 300,
                        "remaining": 300,
                        "percentage_used": 0,
                        "would_exceed": True,
                        "impact_description": "Exceeds shopping budget by $80",
                    },
                    "affected_goals": [],
                    "purchase_category": "impulse",
                    "financial_health_score": 40,
                },
                "actual_purchase": True,
                "regret_level": 7,
                "user_feedback": "Impulse buy, didn't need it",
            },
            {
                "item_name": "Fancy Brunch",
                "amount": Decimal("95"),
                "category": "dining",
                "reason": "Weekend treat",
                "urgency": "low",
                "score": 5,
                "decision_category": "mild_no",
                "reasoning": "Weekend treats are fine in moderation, but $95 for brunch is nearly half your dining budget.",
                "analysis": {
                    "budget_analysis": {
                        "category": "dining",
                        "current_spent": 0,
                        "limit": 200,
                        "remaining": 200,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 47% of dining budget",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 40,
                },
                "alternatives": [
                    "Choose a $40-50 brunch spot",
                    "Make a special brunch at home",
                ],
                "actual_purchase": True,
                "regret_level": 5,
                "user_feedback": "Could have cooked at home",
            },
            {
                "item_name": "Workout Clothes",
                "amount": Decimal("150"),
                "category": "shopping",
                "reason": "New gym motivation",
                "urgency": "medium",
                "score": 4,
                "decision_category": "mild_no",
                "reasoning": "Buying motivation rarely works. You already have workout clothes. Start with the gym membership first, prove consistency for 3 months, then buy new clothes as a reward.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 380,
                        "limit": 300,
                        "remaining": -80,
                        "percentage_used": 127,
                        "would_exceed": True,
                        "impact_description": "Already over budget, adds another $150",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 35,
                },
                "actual_purchase": True,
                "regret_level": 6,
                "user_feedback": "Still haven't used the gym",
            },
            {
                "item_name": "Streaming Services",
                "amount": Decimal("45"),
                "category": "entertainment",
                "reason": "Multiple subscriptions",
                "urgency": "low",
                "score": 6,
                "decision_category": "neutral",
                "reasoning": "Entertainment is reasonable, but audit if you actually use all subscriptions. Consider sharing with family or rotating services monthly.",
                "analysis": {
                    "budget_analysis": {
                        "category": "entertainment",
                        "current_spent": 0,
                        "limit": 150,
                        "remaining": 150,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 30% of entertainment budget",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 40,
                },
                "actual_purchase": True,
                "regret_level": 3,
                "user_feedback": "At least I use them",
            },
            {
                "item_name": "Gas Station Snacks",
                "amount": Decimal("60"),
                "category": "groceries",
                "reason": "Convenience",
                "urgency": "low",
                "score": 4,
                "decision_category": "mild_no",
                "reasoning": "Gas station prices are typically 200-300% higher than grocery stores. Plan ahead and bring snacks.",
                "analysis": {
                    "budget_analysis": {
                        "category": "groceries",
                        "current_spent": 0,
                        "limit": 600,
                        "remaining": 600,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 10% of grocery budget inefficiently",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 40,
                },
                "actual_purchase": True,
                "regret_level": 5,
                "user_feedback": "So expensive for snacks",
            },
            {
                "item_name": "Restaurant Delivery",
                "amount": Decimal("70"),
                "category": "dining",
                "reason": "Working late",
                "urgency": "medium",
                "score": 5,
                "decision_category": "mild_no",
                "reasoning": "Already spent $95 on brunch. With delivery fees, you're at $165 dining spending. Keep some frozen meals for late work nights.",
                "analysis": {
                    "budget_analysis": {
                        "category": "dining",
                        "current_spent": 95,
                        "limit": 200,
                        "remaining": 105,
                        "percentage_used": 47.5,
                        "would_exceed": False,
                        "impact_description": "Brings total dining to $165 (82% of budget)",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 40,
                },
                "actual_purchase": True,
                "regret_level": 4,
                "user_feedback": "Delivery fees add up",
            },
        ],
        # Month 3: Starting to improve
        [
            {
                "item_name": "Quality Winter Coat",
                "amount": Decimal("280"),
                "category": "shopping",
                "reason": "Actually need it for winter",
                "urgency": "high",
                "score": 8,
                "decision_category": "mild_yes",
                "reasoning": "Essential purchase for winter. Quality coat will last years. Good investment compared to cheap coats that need replacing.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 0,
                        "limit": 300,
                        "remaining": 300,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 93% of shopping budget for an essential item",
                    },
                    "affected_goals": [],
                    "purchase_category": "essential",
                    "financial_health_score": 55,
                },
                "actual_purchase": True,
                "regret_level": 2,
                "user_feedback": "Worth it, will last years",
            },
            {
                "item_name": "Birthday Dinner",
                "amount": Decimal("85"),
                "category": "dining",
                "reason": "Friend's birthday",
                "urgency": "high",
                "score": 7,
                "decision_category": "mild_yes",
                "reasoning": "Celebrating relationships is worthwhile. This is a reasonable amount for a special occasion.",
                "analysis": {
                    "budget_analysis": {
                        "category": "dining",
                        "current_spent": 0,
                        "limit": 200,
                        "remaining": 200,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 42% of dining budget for special occasion",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 55,
                },
                "actual_purchase": True,
                "regret_level": 2,
                "user_feedback": "Special occasion, no regrets",
            },
            {
                "item_name": "Impulse Jewelry",
                "amount": Decimal("120"),
                "category": "shopping",
                "reason": "On sale",
                "urgency": "low",
                "score": 3,
                "decision_category": "strong_no",
                "reasoning": "You already spent $280 on a coat (93% of shopping budget). 'On sale' is not a reason to buy. Saved money is better than spent money on sale items you don't need.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 280,
                        "limit": 300,
                        "remaining": 20,
                        "percentage_used": 93,
                        "would_exceed": True,
                        "impact_description": "Would exceed budget by $100",
                    },
                    "affected_goals": [],
                    "purchase_category": "impulse",
                    "financial_health_score": 55,
                },
                "alternatives": [
                    "Wait until next month if you still want it",
                    "Save the $120 toward emergency fund",
                ],
                "conditions": [
                    "You receive unexpected income",
                    "Next month's budget allows for it",
                ],
                "actual_purchase": False,
                "user_feedback": "AI convinced me to wait",
            },
            {
                "item_name": "Movie Night",
                "amount": Decimal("50"),
                "category": "entertainment",
                "reason": "Date night",
                "urgency": "medium",
                "score": 7,
                "decision_category": "mild_yes",
                "reasoning": "Reasonable entertainment expense for quality time. Much better value than the VIP concert tickets from month 1.",
                "analysis": {
                    "budget_analysis": {
                        "category": "entertainment",
                        "current_spent": 0,
                        "limit": 150,
                        "remaining": 150,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 33% of entertainment budget",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 55,
                },
                "actual_purchase": True,
                "regret_level": 2,
                "user_feedback": "Good quality time",
            },
            {
                "item_name": "Grocery Shopping",
                "amount": Decimal("180"),
                "category": "groceries",
                "reason": "Meal prep for week",
                "urgency": "high",
                "score": 9,
                "decision_category": "strong_yes",
                "reasoning": "Excellent! Meal prepping saves money on dining and reduces food waste. This directly addresses your previous pattern of expensive takeout.",
                "analysis": {
                    "budget_analysis": {
                        "category": "groceries",
                        "current_spent": 0,
                        "limit": 600,
                        "remaining": 600,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 30% of grocery budget wisely",
                    },
                    "affected_goals": [],
                    "purchase_category": "essential",
                    "financial_health_score": 60,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Saved money cooking at home",
            },
            {
                "item_name": "Coffee Subscription",
                "amount": Decimal("40"),
                "category": "dining",
                "reason": "Daily coffee habit",
                "urgency": "low",
                "score": 5,
                "decision_category": "mild_no",
                "reasoning": "Already spent $85 on birthday dinner. Making coffee at home would save more. If you must have premium coffee, this is better than daily cafe visits.",
                "analysis": {
                    "budget_analysis": {
                        "category": "dining",
                        "current_spent": 85,
                        "limit": 200,
                        "remaining": 115,
                        "percentage_used": 42.5,
                        "would_exceed": False,
                        "impact_description": "Adds 20% to dining spending",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 58,
                },
                "alternatives": [
                    "Buy coffee beans and make at home",
                    "Limit subscription to every other month",
                ],
                "actual_purchase": False,
                "user_feedback": "Decided to make coffee at home",
            },
        ],
        # Month 4: Much better control
        [
            {
                "item_name": "Work Laptop Upgrade",
                "amount": Decimal("350"),
                "category": "shopping",
                "reason": "Needed for productivity",
                "urgency": "high",
                "score": 8,
                "decision_category": "mild_yes",
                "reasoning": "Tools that improve productivity are good investments. This exceeds shopping budget but is essential for work.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 0,
                        "limit": 300,
                        "remaining": 300,
                        "percentage_used": 0,
                        "would_exceed": True,
                        "impact_description": "Exceeds shopping budget by $50 for essential work tool",
                    },
                    "affected_goals": [],
                    "purchase_category": "investment",
                    "financial_health_score": 65,
                },
                "conditions": [
                    "Can be used as business expense deduction",
                    "Significantly improves work efficiency",
                ],
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Essential purchase",
            },
            {
                "item_name": "Expensive Restaurant",
                "amount": Decimal("150"),
                "category": "dining",
                "reason": "Anniversary celebration",
                "urgency": "high",
                "score": 8,
                "decision_category": "mild_yes",
                "reasoning": "Special occasions deserve celebration. Important relationships are worth investing in.",
                "analysis": {
                    "budget_analysis": {
                        "category": "dining",
                        "current_spent": 0,
                        "limit": 200,
                        "remaining": 200,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 75% of dining budget for special occasion",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 65,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Worth it for special occasion",
            },
            {
                "item_name": "Trendy Sunglasses",
                "amount": Decimal("180"),
                "category": "shopping",
                "reason": "Saw celebrity wearing them",
                "urgency": "low",
                "score": 2,
                "decision_category": "strong_no",
                "reasoning": "You already spent $350 on laptop. Celebrity endorsements are marketing, not reasons to buy. You're showing great improvement - stay strong!",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 350,
                        "limit": 300,
                        "remaining": -50,
                        "percentage_used": 117,
                        "would_exceed": True,
                        "impact_description": "Would put you $230 over shopping budget",
                    },
                    "affected_goals": [],
                    "purchase_category": "impulse",
                    "financial_health_score": 65,
                },
                "alternatives": [
                    "Find similar sunglasses for $40-60",
                    "Wait for off-season sales",
                ],
                "actual_purchase": False,
                "user_feedback": "Waited and glad I did",
            },
            {
                "item_name": "Gym Membership",
                "amount": Decimal("60"),
                "category": "entertainment",
                "reason": "Health investment",
                "urgency": "medium",
                "score": 8,
                "decision_category": "mild_yes",
                "reasoning": "Much better than buying workout clothes you don't use! Health investments pay dividends. Great decision.",
                "analysis": {
                    "budget_analysis": {
                        "category": "entertainment",
                        "current_spent": 0,
                        "limit": 150,
                        "remaining": 150,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 40% of entertainment budget for health",
                    },
                    "affected_goals": [],
                    "purchase_category": "investment",
                    "financial_health_score": 70,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Using it regularly!",
            },
            {
                "item_name": "Weekly Groceries",
                "amount": Decimal("140"),
                "category": "groceries",
                "reason": "Planned shopping",
                "urgency": "high",
                "score": 9,
                "decision_category": "strong_yes",
                "reasoning": "Planned grocery shopping with a list. You're forming excellent habits!",
                "analysis": {
                    "budget_analysis": {
                        "category": "groceries",
                        "current_spent": 0,
                        "limit": 600,
                        "remaining": 600,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 23% of grocery budget efficiently",
                    },
                    "affected_goals": [],
                    "purchase_category": "essential",
                    "financial_health_score": 70,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Sticking to list helped",
            },
        ],
        # Month 5: Excellent control
        [
            {
                "item_name": "Quality Shoes",
                "amount": Decimal("120"),
                "category": "shopping",
                "reason": "Old ones wore out",
                "urgency": "high",
                "score": 8,
                "decision_category": "mild_yes",
                "reasoning": "Replacing worn-out essentials is smart. Quality shoes are a health investment for your feet and back.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 0,
                        "limit": 300,
                        "remaining": 300,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 40% of shopping budget for essential replacement",
                    },
                    "affected_goals": [],
                    "purchase_category": "essential",
                    "financial_health_score": 75,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Needed replacement",
            },
            {
                "item_name": "Meal Prep Groceries",
                "amount": Decimal("160"),
                "category": "groceries",
                "reason": "Weekly meal plan",
                "urgency": "high",
                "score": 9,
                "decision_category": "strong_yes",
                "reasoning": "You've mastered meal planning! This saves money and improves health. Your transformation from month 1 is impressive.",
                "analysis": {
                    "budget_analysis": {
                        "category": "groceries",
                        "current_spent": 0,
                        "limit": 600,
                        "remaining": 600,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 27% of grocery budget wisely",
                    },
                    "affected_goals": [],
                    "purchase_category": "essential",
                    "financial_health_score": 75,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Saving so much money",
            },
            {
                "item_name": "Designer Bag",
                "amount": Decimal("500"),
                "category": "shopping",
                "reason": "Looks amazing online",
                "urgency": "low",
                "score": 1,
                "decision_category": "strong_no",
                "reasoning": "This is a test of your progress! $500 is 167% of your shopping budget. You've already shown you regret these impulse purchases. Stay strong!",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 120,
                        "limit": 300,
                        "remaining": 180,
                        "percentage_used": 40,
                        "would_exceed": True,
                        "impact_description": "Would exceed budget by $320",
                    },
                    "affected_goals": [
                        {
                            "goal_name": "Emergency Fund",
                            "target_amount": 10000,
                            "current_amount": 4200,
                            "remaining": 5800,
                            "deadline": "2026-12-31",
                            "impact_description": "$500 represents 8.6% of what you still need for emergency fund",
                        }
                    ],
                    "purchase_category": "impulse",
                    "financial_health_score": 75,
                },
                "alternatives": [
                    "Add $500 to emergency fund instead",
                    "Set this as a reward for hitting $6000 in emergency fund",
                ],
                "actual_purchase": False,
                "user_feedback": "Proud of myself for saying no",
            },
            {
                "item_name": "Movie Tickets",
                "amount": Decimal("30"),
                "category": "entertainment",
                "reason": "Budget-friendly date",
                "urgency": "low",
                "score": 8,
                "decision_category": "mild_yes",
                "reasoning": "You've learned to find budget-friendly entertainment! This is exactly the right mindset.",
                "analysis": {
                    "budget_analysis": {
                        "category": "entertainment",
                        "current_spent": 0,
                        "limit": 150,
                        "remaining": 150,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses only 20% of entertainment budget",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 78,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Affordable fun",
            },
        ],
        # Month 6 (Current): Maintaining good habits
        [
            {
                "item_name": "Groceries",
                "amount": Decimal("145"),
                "category": "groceries",
                "reason": "Weekly shopping",
                "urgency": "high",
                "score": 9,
                "decision_category": "strong_yes",
                "reasoning": "Consistent smart grocery shopping. You've built sustainable habits!",
                "analysis": {
                    "budget_analysis": {
                        "category": "groceries",
                        "current_spent": 0,
                        "limit": 600,
                        "remaining": 600,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 24% of grocery budget",
                    },
                    "affected_goals": [],
                    "purchase_category": "essential",
                    "financial_health_score": 80,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Sticking to budget!",
            },
            {
                "item_name": "Coffee Date",
                "amount": Decimal("25"),
                "category": "dining",
                "reason": "Catching up with friend",
                "urgency": "medium",
                "score": 8,
                "decision_category": "mild_yes",
                "reasoning": "Social connections matter. This is a reasonable amount for quality time with friends.",
                "analysis": {
                    "budget_analysis": {
                        "category": "dining",
                        "current_spent": 0,
                        "limit": 200,
                        "remaining": 200,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 12% of dining budget",
                    },
                    "affected_goals": [],
                    "purchase_category": "discretionary",
                    "financial_health_score": 80,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Affordable and fun",
            },
            {
                "item_name": "New Phone",
                "amount": Decimal("800"),
                "category": "shopping",
                "reason": "Latest model released",
                "urgency": "low",
                "score": 3,
                "decision_category": "strong_no",
                "reasoning": "Latest model is not a need. Unless your current phone is broken, this is $800 that could go to your house down payment goal. You're at 267% of shopping budget.",
                "analysis": {
                    "budget_analysis": {
                        "category": "shopping",
                        "current_spent": 0,
                        "limit": 300,
                        "remaining": 300,
                        "percentage_used": 0,
                        "would_exceed": True,
                        "impact_description": "Would exceed budget by $500",
                    },
                    "affected_goals": [
                        {
                            "goal_name": "House Down Payment",
                            "target_amount": 50000,
                            "current_amount": 18500,
                            "remaining": 31500,
                            "deadline": "2028-06-30",
                            "impact_description": "$800 represents 2.5% of remaining down payment goal",
                        }
                    ],
                    "purchase_category": "discretionary",
                    "financial_health_score": 80,
                },
                "alternatives": [
                    "Wait for current phone to actually break",
                    "Buy last year's model for 40% less",
                    "Add $800 to down payment fund",
                ],
                "conditions": [
                    "Current phone is actually broken beyond repair",
                    "You receive a work bonus specifically for equipment",
                ],
            },
            {
                "item_name": "Yoga Classes",
                "amount": Decimal("80"),
                "category": "entertainment",
                "reason": "Health and wellness",
                "urgency": "medium",
                "score": 8,
                "decision_category": "mild_yes",
                "reasoning": "Mental health and physical wellness are worthwhile investments. You're using your entertainment budget wisely.",
                "analysis": {
                    "budget_analysis": {
                        "category": "entertainment",
                        "current_spent": 0,
                        "limit": 150,
                        "remaining": 150,
                        "percentage_used": 0,
                        "would_exceed": False,
                        "impact_description": "Uses 53% of entertainment budget for wellness",
                    },
                    "affected_goals": [],
                    "purchase_category": "investment",
                    "financial_health_score": 80,
                },
                "actual_purchase": True,
                "regret_level": 1,
                "user_feedback": "Great for mental health",
            },
        ],
    ]

    for month_idx, (year, month, name) in enumerate(months):
        period_start, period_end = get_budget_period(year, month, 1)
        decisions = purchase_patterns[month_idx]

        # Initialize categories with zero spent (will be updated by budget items)
        categories = {k: dict(v) for k, v in base_categories.items()}

        # Create budget
        budget = create_budget(
            db,
            user.user_id,
            f"{name} Budget",
            Decimal("1650"),
            period_start,
            period_end,
            categories,
        )
        print(f"    ✓ Created budget for {name}")

        # Create decisions
        for idx, dec in enumerate(decisions):
            # Spread decisions throughout the month
            days_in_month = (period_end - period_start).days
            day_offset = (
                (days_in_month // len(decisions)) * idx if len(decisions) > 0 else 0
            )
            transaction_date = datetime(year, month, 1) + timedelta(days=day_offset)

            create_decision(
                db,
                user.user_id,
                item_name=dec["item_name"],
                amount=dec["amount"],
                category=dec["category"],
                reason=dec["reason"],
                urgency=dec["urgency"],
                score=dec["score"],
                decision_category=dec["decision_category"],
                reasoning=dec["reasoning"],
                analysis=dec["analysis"],
                alternatives=dec.get("alternatives"),
                conditions=dec.get("conditions"),
                actual_purchase=dec.get("actual_purchase"),
                regret_level=dec.get("regret_level"),
                user_feedback=dec.get("user_feedback"),
                budget_id=budget.budget_id,
                transaction_date=transaction_date,
                created_at=transaction_date,
                updated_at=transaction_date,
            )

        print(f"    ✓ Created {len(decisions)} decisions for {name}")

    # Create goals
    print("  🎯 Creating Sarah's goals...")
    create_goal(
        db,
        user.user_id,
        "Emergency Fund",
        Decimal("10000"),
        Decimal("4200"),
        "high",
        date(2026, 12, 31),
    )
    create_goal(
        db,
        user.user_id,
        "House Down Payment",
        Decimal("50000"),
        Decimal("18500"),
        "high",
        date(2028, 6, 30),
    )


def main():
    """Main seeding function."""
    print("🌱 Seeding demo data directly to database...\n")

    db = SessionLocal()
    try:
        # Sarah - Impulsive buyer improving over time
        print("👤 Setting up Sarah Chen (Impulsive Buyer → Improving)...")
        sarah = create_user(
            db,
            "demo+sarah@fiscalguard.app",
            "demo123",
            "Sarah Chen",
            "financial_monk",
            9,
        )
        seed_sarah(db, sarah)
        print("  ✅ Sarah complete (36 decisions across 6 months)\n")

        print("✨ Demo data seeding complete!\n")
        print("📝 Demo Account:")
        print("  - Sarah: demo+sarah@fiscalguard.app / demo123 (Financial Monk 9/10)")
        print("    Budget resets: 1st of each month")
        print("    Pattern: Started overspending, improved over 6 months\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
