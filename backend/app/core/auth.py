"""Authentication and ownership abstraction (JWT Bearer tokens).

In production (or when security_mode == "enforced"), requests to protected
endpoints MUST provide a valid Bearer JWT. In development demo mode, unauthenticated
requests fall back to a deterministic local user ID ('demo-user-local') for developer
convenience without compromising production security boundaries.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)

DEMO_USER_ID = "demo-user-local"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    expires_at: datetime


def create_access_token(
    user_id: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Generate a signed JWT for the specified user_id."""
    settings = get_settings()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_expire_minutes)

    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "idealens-api",
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed JWT. Raises HTTPException(401) on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer="idealens-api",
            options={"require": ["exp", "iat", "sub"]},
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """FastAPI dependency resolving the authenticated user's ID.

    Guarantees:
    - If valid Bearer token provided: returns subject user ID.
    - If invalid token provided: raises HTTP 401.
    - If no token provided and auth is enforced: raises HTTP 401.
    - If no token provided in development mode: returns DEMO_USER_ID.
    """
    settings = get_settings()

    if authorization is not None:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            payload = decode_access_token(token)
            user_id = str(payload.get("sub", "")).strip()
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Malformed token: missing subject identity.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user_id
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Must be 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # No authorization header provided
    if settings.is_auth_enforced:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Authentication required. Provide a valid Bearer token in the "
                "Authorization header."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Insecure local development fallback
    return DEMO_USER_ID


CurrentUser = Annotated[str, Depends(get_current_user_id)]
