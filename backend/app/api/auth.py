import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.deps import get_current_username
from app.auth.security import COOKIE_NAME, create_access_token, verify_password
from app.config import get_settings
from app.db import get_session, get_write_session
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory sliding-window limiter, keyed by client IP. A single-process
# backend is all this deployment ever runs, so no shared store is needed.
_login_attempts: dict[str, deque] = defaultdict(deque)


def _check_login_rate_limit(client_ip: str) -> None:
    settings = get_settings()
    now = time.monotonic()
    window_start = now - settings.login_rate_limit_window_seconds
    attempts = _login_attempts[client_ip]
    while attempts and attempts[0] < window_start:
        attempts.popleft()
    if len(attempts) >= settings.login_rate_limit_attempts:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas de login. Aguarde alguns minutos.",
        )
    attempts.append(now)


@router.post("/login", response_model=MeResponse)
def login(payload: LoginRequest, request: Request, response: Response):
    client_ip = request.client.host if request.client else "unknown"
    _check_login_rate_limit(client_ip)

    with get_session() as session:
        user = session.query(User).filter(User.username == payload.username).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    with get_write_session() as session:
        db_user = session.query(User).filter(User.id == user.id).first()
        db_user.last_login_at = datetime.now(timezone.utc)

    token = create_access_token(subject=user.username)
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.netsentinel_env == "production",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return MeResponse(username=user.username)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
def me(username: str = Depends(get_current_username)):
    return MeResponse(username=username)
