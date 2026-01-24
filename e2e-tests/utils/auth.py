"""
Authentication utilities for E2E tests
"""

import os
import httpx
from playwright.sync_api import Page

API_URL = os.getenv("API_URL", "http://localhost:8000")


def login_via_api(email: str, password: str) -> str:
    """Login via API and get JWT token"""
    response = httpx.post(
        f"{API_URL}/auth/login",
        data={"username": email, "password": password},
    )
    response.raise_for_status()
    return response.json()["access_token"]


def inject_auth_token(page: Page, token: str) -> None:
    """
    Inject auth token into browser storage
    This bypasses the login UI and directly sets the auth state
    """
    # Add cookie
    page.context.add_cookies([
        {
            "name": "auth_token",
            "value": token,
            "domain": "localhost",
            "path": "/",
            "httpOnly": False,
            "secure": False,
            "sameSite": "Lax",
        }
    ])

    # Also inject into localStorage if the app uses it
    page.add_init_script(f"""
        localStorage.setItem('auth_token', '{token}');
        localStorage.setItem('token', '{token}');
    """)


def setup_authenticated_session(page: Page, email: str, password: str) -> str:
    """Setup authenticated session for a user"""
    token = login_via_api(email, password)
    inject_auth_token(page, token)
    return token


def get_user_info(token: str) -> dict:
    """Get user info from token"""
    response = httpx.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()


def is_authenticated(page: Page) -> bool:
    """Check if user is authenticated"""
    cookies = page.context.cookies()
    auth_cookie = any(c["name"] == "auth_token" for c in cookies)

    if not auth_cookie:
        token = page.evaluate("""
            () => localStorage.getItem('auth_token') || localStorage.getItem('token')
        """)
        return bool(token)

    return True


def logout(page: Page) -> None:
    """Logout by clearing auth state"""
    page.context.clear_cookies()
    page.evaluate("""
        () => {
            localStorage.clear();
            sessionStorage.clear();
        }
    """)
