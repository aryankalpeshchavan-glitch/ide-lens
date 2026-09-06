"""Authentication endpoints: token issuance and current session introspection."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.auth import CurrentUser, TokenResponse, create_access_token
from app.core.config import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class TokenRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128, description="User identity handle")


class SessionInfoResponse(BaseModel):
    user_id: str
    security_mode: str
    auth_enforced: bool


@router.post("/token", response_model=TokenResponse)
def issue_token(request: TokenRequest) -> TokenResponse:
    """Issue a signed Bearer JWT token for a given user identifier."""
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.jwt_expire_minutes)
    token = create_access_token(request.user_id, expires_delta=expires_delta)
    expires_at = datetime.now(UTC) + expires_delta
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=request.user_id,
        expires_at=expires_at,
    )


@router.get("/me", response_model=SessionInfoResponse)
def get_current_session(user_id: CurrentUser) -> SessionInfoResponse:
    """Return the currently authenticated identity and security posture."""
    settings = get_settings()
    return SessionInfoResponse(
        user_id=user_id,
        security_mode=settings.security_mode,
        auth_enforced=settings.is_auth_enforced,
    )
