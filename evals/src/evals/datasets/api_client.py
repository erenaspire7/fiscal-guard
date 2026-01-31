"""API client for interacting with Fiscal Guard API."""

from typing import Any, Dict, List, Optional

import httpx


class FiscalGuardAPIClient:
    """Client for interacting with Fiscal Guard API."""

    def __init__(self, api_url: str, timeout: float = 30.0):
        """Initialize API client.

        Args:
            api_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def send_chat_message(
        self,
        message: str,
        token: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to the chat endpoint.

        Args:
            message: User's message
            token: JWT access token
            conversation_history: Previous conversation messages
            session_id: Optional session ID for prompt override testing

        Returns:
            API response as dict

        Raises:
            httpx.HTTPError: If request fails
        """
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "message": message,
            "conversation_history": conversation_history or [],
        }

        if session_id:
            payload["session_id"] = session_id

        response = httpx.post(
            f"{self.api_url}/chat/message",
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()
        return response.json()

    def set_prompt_override(
        self,
        agent_type: str,
        prompt: str,
        session_id: str,
        internal_token: str,
    ) -> Dict[str, Any]:
        """Set a prompt override for testing.

        Args:
            agent_type: Type of agent (decision_agent, intent_classifier)
            prompt: Prompt text to use
            session_id: Unique session ID for this override
            internal_token: Internal API token for authentication

        Returns:
            API response

        Raises:
            httpx.HTTPError: If request fails
        """
        headers = {"X-Internal-Token": internal_token}

        payload = {
            "agent_type": agent_type,
            "prompt": prompt,
            "session_id": session_id,
        }

        response = httpx.post(
            f"{self.api_url}/internal/set-prompt",
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """Check if API is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = httpx.get(f"{self.api_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
