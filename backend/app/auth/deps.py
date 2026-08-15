from fastapi import Cookie, HTTPException, status

from app.auth.security import COOKIE_NAME, decode_access_token


async def get_current_username(
    netsentinel_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> str:
    if not netsentinel_session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    username = decode_access_token(netsentinel_session)
    if not username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    return username
