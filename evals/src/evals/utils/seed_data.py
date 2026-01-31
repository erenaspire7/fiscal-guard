"""
Seed demo data directly into the database.

This script bypasses the API endpoints and directly inserts records,
avoiding AI agent evaluation delays during seeding.
"""

import json
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

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


def generate_months(num_months: int = 6) -> list[tuple[int, int, str]]:
    """Generate list of (year, month, name) tuples for the past N-1 months plus next month.

    This ensures the most recent budget extends into the future and remains active
    during evaluation runs.
    """
    months = []
    today = datetime.utcnow()

    # Generate past months (num_months - 2) + current month + next month
    # This gives us historical data plus an active budget
    for i in range(num_months - 2, -2, -1):  # Changed range to include next month
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        months.append((y, m, datetime(y, m, 1).strftime("%B %Y")))
    return months


def load_character_data(character_name: str) -> dict:
    """Load and process character data from JSON file."""
    json_path = Path(__file__).parent.parent / "personas" / f"{character_name}.json"
    with open(json_path, "r") as f:
        character_data = json.load(f)

    # Convert string/numeric amounts to Decimal for database insertion
    purchase_patterns = []
    for month_purchases in character_data["purchase_patterns"]:
        month_data = []
        for purchase in month_purchases:
            purchase_copy = purchase.copy()
            purchase_copy["amount"] = Decimal(str(purchase["amount"]))
            month_data.append(purchase_copy)
        purchase_patterns.append(month_data)

    character_data["purchase_patterns"] = purchase_patterns
    return character_data


def seed_character_data(
    db,
    user: User,
    character_data: dict,
    total_monthly: Decimal,
    months: list[tuple[int, int, str]],
):
    """Generic function to seed character budgets and decisions."""
    print("  📊 Creating 6 months of budgets and decisions...")

    base_categories = character_data["base_categories"]
    purchase_patterns = character_data["purchase_patterns"]

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
            total_monthly,
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


def seed_sarah(db, user: User):
    """
    Seed Sarah's data - Impulsive buyer improving over time.

    Month-by-month spending pattern evolution:
    - Months 1-2: Heavy overspending on impulse purchases
    - Month 3: Starting to improve with some good decisions
    - Months 4-6: Much better control, saying no to impulse buys
    """
    character_data = load_character_data("sarah")
    months = generate_months(6)
    seed_character_data(db, user, character_data, Decimal("1650"), months)

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


def seed_alex(db, user: User):
    """
    Seed Alex's data - Balanced spender with good habits.

    Month-by-month spending pattern:
    - Months 1-6: Consistent smart spending with occasional splurges
    - Maintains budgets well and makes thoughtful decisions
    - Prioritizes essentials and investments over impulse purchases
    """
    character_data = load_character_data("alex")
    months = generate_months(6)
    seed_character_data(db, user, character_data, Decimal("1480"), months)

    # Create goals
    print("  🎯 Creating Alex's goals...")
    create_goal(
        db,
        user.user_id,
        "Vacation Fund",
        Decimal("8000"),
        Decimal("5200"),
        "medium",
        date(2026, 9, 1),
    )
    create_goal(
        db,
        user.user_id,
        "Investment Account",
        Decimal("15000"),
        Decimal("9800"),
        "high",
        date(2027, 12, 31),
    )


def seed_marcus(db, user: User):
    """
    Seed Marcus's data - Financial Monk with excellent spending discipline.

    Month-by-month spending pattern:
    - Months 1-6: Consistent disciplined spending with smart decisions
    - Says no to impulse purchases and luxury items
    - Prioritizes essentials, health, and personal growth
    """
    character_data = load_character_data("marcus")
    months = generate_months(6)
    seed_character_data(db, user, character_data, Decimal("1480"), months)

    # Create goals
    print("  🎯 Creating Marcus's goals...")
    create_goal(
        db,
        user.user_id,
        "Vacation Fund",
        Decimal("8000"),
        Decimal("5200"),
        "medium",
        date(2026, 9, 1),
    )
    create_goal(
        db,
        user.user_id,
        "Investment Account",
        Decimal("15000"),
        Decimal("9800"),
        "high",
        date(2027, 12, 31),
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

        # Alex - Balanced spender
        print("👤 Setting up Alex Rivera (Balanced Spender)...")
        alex = create_user(
            db,
            "demo+alex@fiscalguard.app",
            "demo123",
            "Alex Rivera",
            "financial_monk",
            8,
        )
        seed_alex(db, alex)
        print("  ✅ Alex complete (36 decisions across 6 months)\n")

        # Marcus - Financial Monk with excellent discipline
        print("👤 Setting up Marcus Thompson (Financial Monk)...")
        marcus = create_user(
            db,
            "demo+marcus@fiscalguard.app",
            "demo123",
            "Marcus Thompson",
            "financial_monk",
            10,
        )
        seed_marcus(db, marcus)
        print("  ✅ Marcus complete (36 decisions across 6 months)\n")

        print("✨ Demo data seeding complete!\n")
        print("📝 Demo Accounts:")
        print("  - Sarah: demo+sarah@fiscalguard.app / demo123 (Financial Monk 9/10)")
        print("    Budget resets: 1st of each month")
        print("    Pattern: Started overspending, improved over 6 months")
        print("  - Alex: demo+alex@fiscalguard.app / demo123 (Financial Monk 8/10)")
        print("    Budget resets: 1st of each month")
        print("    Pattern: Consistent balanced spending with good habits")
        print(
            "  - Marcus: demo+marcus@fiscalguard.app / demo123 (Financial Monk 10/10)"
        )
        print("    Budget resets: 1st of each month")
        print("    Pattern: Excellent spending discipline with smart decisions\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
