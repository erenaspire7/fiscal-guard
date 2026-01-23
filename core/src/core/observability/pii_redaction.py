"""PII redaction utilities for observability and tracing.

This module provides utilities to redact personally identifiable information (PII)
before sending data to observability platforms like Opik.
"""

import re
from typing import Any, Dict, Optional


class PIIRedactor:
    """Utilities for redacting PII from trace data."""

    @staticmethod
    def redact_pii(data: Any) -> Any:
        """Redact PII from data before sending to observability platform.

        Redacts:
        - Email addresses
        - User IDs (UUIDs)
        - Financial amounts (keeps only rounded values)
        - User names

        Args:
            data: Data to redact

        Returns:
            Redacted data
        """
        if isinstance(data, str):
            # Redact email addresses
            data = re.sub(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "[EMAIL_REDACTED]",
                data,
            )

            # Redact UUIDs
            data = re.sub(
                r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                "[UUID_REDACTED]",
                data,
            )

            # Redact specific dollar amounts (keep rounded)
            data = re.sub(
                r"\$\d+\.\d{2}",
                lambda m: f"${round(float(m.group()[1:]), -1):.0f}",
                data,
            )

            return data

        elif isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                # Redact sensitive keys entirely
                if key.lower() in ["email", "user_id", "full_name", "profile_picture"]:
                    redacted[key] = "[REDACTED]"
                elif key.lower() in [
                    "amount",
                    "limit",
                    "spent",
                    "target_amount",
                    "current_amount",
                ]:
                    # Round financial amounts to nearest 10
                    if isinstance(value, (int, float)):
                        redacted[key] = round(value, -1)
                    else:
                        redacted[key] = PIIRedactor.redact_pii(value)
                else:
                    redacted[key] = PIIRedactor.redact_pii(value)
            return redacted

        elif isinstance(data, list):
            return [PIIRedactor.redact_pii(item) for item in data]

        else:
            return data

    @staticmethod
    def create_trace_attributes(
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        category: Optional[str] = None,
        amount: Optional[float] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create trace attributes for Strands Agent with PII redaction.

        This creates the trace_attributes dictionary that gets passed to
        the Strands Agent constructor. All PII is automatically redacted.

        Args:
            user_id: User ID (will be redacted to "[USER_REDACTED]")
            session_id: Session ID for grouping related traces
            category: Purchase category (not PII, passed through)
            amount: Purchase amount (will be converted to range)
            **kwargs: Additional metadata (will be redacted if contains PII)

        Returns:
            Dictionary of trace attributes safe to send to observability platform

        Example:
            >>> attributes = PIIRedactor.create_trace_attributes(
            ...     user_id="123e4567-e89b-12d3-a456-426614174000",
            ...     session_id="session-abc",
            ...     category="groceries",
            ...     amount=45.67
            ... )
            >>> # Returns: {
            ...     "user.id": "[USER_REDACTED]",
            ...     "session.id": "session-abc",
            ...     "category": "groceries",
            ...     "amount_range": "$0-50"
            ... }
        """
        attributes = {}

        # Redact user_id
        if user_id:
            attributes["user.id"] = "[USER_REDACTED]"

        # Session ID is generally safe (doesn't contain PII)
        if session_id:
            attributes["session.id"] = session_id

        # Category is safe
        if category:
            attributes["category"] = category

        # Convert amount to range for privacy
        if amount is not None:
            attributes["amount_range"] = PIIRedactor._get_amount_range(amount)

        # Redact any additional kwargs
        for key, value in kwargs.items():
            if isinstance(value, str) and any(
                pii in key.lower() for pii in ["email", "name", "user"]
            ):
                attributes[key] = "[REDACTED]"
            else:
                attributes[key] = PIIRedactor.redact_pii(value)

        return attributes

    @staticmethod
    def _get_amount_range(amount: float) -> str:
        """Get amount range for grouping without exposing exact amounts.

        Args:
            amount: Exact amount

        Returns:
            Range string (e.g., "$0-50", "$50-100")
        """
        if amount < 50:
            return "$0-50"
        elif amount < 100:
            return "$50-100"
        elif amount < 250:
            return "$100-250"
        elif amount < 500:
            return "$250-500"
        else:
            return "$500+"


# Convenience functions for common use cases
def redact_pii(data: Any) -> Any:
    """Convenience function to redact PII from any data structure.

    Args:
        data: Data to redact

    Returns:
        Redacted data
    """
    return PIIRedactor.redact_pii(data)


def create_trace_attributes(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    category: Optional[str] = None,
    amount: Optional[float] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create trace attributes with PII redaction.

    Args:
        user_id: User ID (will be redacted)
        session_id: Session ID
        category: Purchase category
        amount: Purchase amount (will be converted to range)
        **kwargs: Additional metadata

    Returns:
        Dictionary of trace attributes
    """
    return PIIRedactor.create_trace_attributes(
        user_id=user_id,
        session_id=session_id,
        category=category,
        amount=amount,
        **kwargs,
    )
