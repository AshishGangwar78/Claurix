"""
Shared FastAPI dependencies.

Auth is optional today (AUTH_ENABLED=false). When enabled, a Bearer token
is required; replace decode logic with the platform JWT verifier later.
"""

from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status

from backend.core.settings import get_settings


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    settings = get_settings()

    if not settings.auth_enabled:
        # Passthrough identity for local / pre-auth environments
        return {
            "user_id": "anonymous",
            "authenticated": False,
        }

    if not authorization or not authorization.startswith(
        settings.auth_optional_bearer_prefix
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[len(settings.auth_optional_bearer_prefix) :].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )

    # Placeholder: integrate existing platform JWT validation here.
    return {
        "user_id": "token_user",
        "authenticated": True,
        "token": token,
    }


def get_optional_case_id(
    x_case_id: Optional[str] = Header(default=None, alias="X-Case-Id"),
) -> Optional[str]:
    """Active case context from header (frontend/backend may also send in body)."""
    return x_case_id
