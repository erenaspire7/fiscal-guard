"""Opik observability configuration for Fiscal Guard."""

import re
from typing import Any, Dict, Optional

from opik import Opik, track

from core.config import settings


class OpikConfig:
    """Configure Opik for tracing and observability."""

    def __init__(self):
        """Initialize Opik configuration."""
        self.client: Optional[Opik] = None
        self.enabled = bool(settings.opik_api_key)

        if self.enabled:
            try:
                self.client = Opik(
                    api_key=settings.opik_api_key,
                    workspace=settings.opik_workspace,
                )
                print(f"✅ Opik initialized (workspace: {settings.opik_workspace})")
            except Exception as e:
                print(f"⚠️  Opik initialization failed: {e}")
                self.enabled = False
        else:
            print("ℹ️  Opik disabled (no API key)")

    @staticmethod
    def redact_pii(data: Any) -> Any:
        """Redact PII from data before sending to Opik.

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
                        redacted[key] = OpikConfig.redact_pii(value)
                else:
                    redacted[key] = OpikConfig.redact_pii(value)
            return redacted

        elif isinstance(data, list):
            return [OpikConfig.redact_pii(item) for item in data]

        else:
            return data

    def create_trace_metadata(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        amount: Optional[float] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create metadata for a trace with PII redaction.

        Args:
            user_id: User ID (will be redacted)
            category: Purchase category
            amount: Purchase amount (will be rounded)
            **kwargs: Additional metadata

        Returns:
            Redacted metadata dictionary
        """
        metadata = {
            "user_id": "[REDACTED]" if user_id else None,
            "category": category,
            "amount_range": self._get_amount_range(amount) if amount else None,
            **kwargs,
        }

        # Remove None values
        return {k: v for k, v in metadata.items() if v is not None}

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


# Global Opik instance
opik_config = OpikConfig()


# Export decorators for easy use
def track_decision(name: Optional[str] = None):
    """Decorator to track decision-related functions.

    Args:
        name: Optional name for the trace

    Returns:
        Decorator function
    """
    if not opik_config.enabled:
        # No-op decorator if Opik is disabled
        def decorator(func):
            return func

        return decorator

    return track(name=name)


def track_tool(name: Optional[str] = None):
    """Decorator to track tool executions.

    Args:
        name: Optional name for the trace

    Returns:
        Decorator function
    """
    if not opik_config.enabled:

        def decorator(func):
            return func

        return decorator

    return track(name=name, metadata={"type": "tool"})
