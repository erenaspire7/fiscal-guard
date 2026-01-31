"""Authentication helpers for API interactions."""

import httpx


class AuthClient:
    """Handle authentication with the API."""

    def __init__(self, api_url: str):
        """Initialize auth client.

        Args:
            api_url: Base URL for the API
        """
        self.api_url = api_url.rstrip("/")
        self._tokens = {}  # Cache tokens by email

    def login(self, email: str, password: str) -> str:
        """Login and get JWT token.

        Args:
            email: User email
            password: User password

        Returns:
            JWT access token

        Raises:
            httpx.HTTPError: If login fails
        """
        # Check cache first
        if email in self._tokens:
            return self._tokens[email]

        # Login via API
        response = httpx.post(
            f"{self.api_url}/auth/login",
            json={"email": email, "password": password},
        )
        response.raise_for_status()

        token = response.json()["access_token"]
        self._tokens[email] = token
        return token

    def get_persona_credentials(self, persona: str) -> tuple[str, str]:
        """Get login credentials for a persona.

        Args:
            persona: Persona name (sarah, alex, marcus)

        Returns:
            Tuple of (email, password)

        Raises:
            ValueError: If persona is unknown
        """
        credentials = {
            "sarah": ("demo+sarah@fiscalguard.app", "demo123"),
            "alex": ("demo+alex@fiscalguard.app", "demo123"),
            "marcus": ("demo+marcus@fiscalguard.app", "demo123"),
        }

        if persona not in credentials:
            raise ValueError(
                f"Unknown persona: {persona}. Must be one of: {list(credentials.keys())}"
            )

        return credentials[persona]

    def login_as_persona(self, persona: str) -> str:
        """Login as a specific persona.

        Args:
            persona: Persona name (sarah, alex, marcus)

        Returns:
            JWT access token

        Raises:
            ValueError: If persona is unknown
            httpx.HTTPError: If login fails
        """
        email, password = self.get_persona_credentials(persona)
        return self.login(email, password)
