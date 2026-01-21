"""SQLAlchemy database models for Fiscal Guard."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for authentication and profile."""

    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    profile_picture = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    budgets = relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan"
    )
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    decisions = relationship(
        "PurchaseDecision", back_populates="user", cascade="all, delete-orphan"
    )


class Budget(Base):
    """Budget model for tracking spending limits by category."""

    __tablename__ = "budgets"

    budget_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., "January 2026 Budget"
    total_monthly = Column(Numeric(10, 2), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    categories = Column(JSON, nullable=False)
    # Example: {"groceries": {"limit": 500, "spent": 250}, "clothes": {"limit": 300, "spent": 400}}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="budgets")


class Goal(Base):
    """Goal model for tracking financial goals."""

    __tablename__ = "goals"

    goal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    goal_name = Column(String(255), nullable=False)
    target_amount = Column(Numeric(10, 2), nullable=False)
    current_amount = Column(Numeric(10, 2), default=0, nullable=False)
    priority = Column(String(50), default="medium")  # high/medium/low
    deadline = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="goals")


class PurchaseDecision(Base):
    """Purchase decision model for tracking AI-assisted purchase decisions."""

    __tablename__ = "purchase_decisions"

    decision_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    item_name = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=True)  # Budget category
    reason = Column(Text, nullable=True)  # Why user wants to buy
    urgency = Column(String(100), nullable=True)  # Urgency level

    # Decision results
    score = Column(Integer, nullable=False)  # 1-10 score
    decision_category = Column(String(50), nullable=False)  # strong_no, mild_no, etc.
    reasoning = Column(Text, nullable=False)  # AI reasoning
    analysis = Column(JSON, nullable=False)  # Detailed analysis
    alternatives = Column(JSON, nullable=True)  # Alternative suggestions
    conditions = Column(JSON, nullable=True)  # Conditions for better decision

    # User feedback
    actual_purchase = Column(Boolean, nullable=True)  # Did they actually buy it?
    regret_level = Column(Integer, nullable=True)  # 1-10 if purchased
    user_feedback = Column(Text, nullable=True)  # Free-form feedback

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="decisions")
