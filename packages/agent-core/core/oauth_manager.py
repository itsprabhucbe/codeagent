"""
GitHub OAuth authentication manager.
"""
import os
import logging
import httpx
from typing import Optional, Dict, Any
from jose import jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GitHubOAuthManager:
    """Manages GitHub OAuth flow and token management."""

    def __init__(self):
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.callback_url = os.getenv("GITHUB_CALLBACK_URL")
        self.session_secret = os.getenv("SESSION_SECRET")

        if not all([self.client_id, self.client_secret, self.callback_url, self.session_secret]):
            raise ValueError("Missing GitHub OAuth configuration in environment variables")

    def get_authorization_url(self, state: str) -> str:
        """
        Generate GitHub authorization URL.

        Args:
            state: Random state string for CSRF protection

        Returns:
            GitHub authorization URL
        """
        scope = "repo"
        return (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.callback_url}&"
            f"scope={scope}&"
            f"state={state}"
        )

    async def exchange_code_for_token(self, code: str) -> Optional[str]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from GitHub

        Returns:
            Access token if successful, None otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": self.callback_url
                    },
                    headers={"Accept": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    access_token = data.get("access_token")

                    if access_token:
                        logger.info("Successfully exchanged code for access token")
                        return access_token
                    else:
                        logger.error(f"No access token in response: {data}")
                        return None
                else:
                    logger.error(f"Failed to exchange code: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}", exc_info=True)
            return None

    async def get_github_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get GitHub user information."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )

                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(f"Retrieved GitHub user: {user_data.get('login')}")
                    return user_data
                else:
                    logger.error(f"Failed to get user: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error getting GitHub user: {e}", exc_info=True)
            return None

    def create_session_token(self, github_token: str, user_data: Dict[str, Any]) -> str:
        """Create encrypted session token containing GitHub access token."""
        payload = {
            "github_token": github_token,
            "github_user": user_data.get("login"),
            "github_id": user_data.get("id"),
            "exp": datetime.utcnow() + timedelta(days=30)
        }

        token = jwt.encode(payload, self.session_secret, algorithm="HS256")
        logger.info(f"Created session token for user: {user_data.get('login')}")
        return token

    def decode_session_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate session token."""
        try:
            payload = jwt.decode(session_token, self.session_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Session token expired")
            return None
        except jwt.JWTError as e:
            logger.error(f"Invalid session token: {e}")
            return None
