"""HMAC bearer token verification middleware."""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param

from app.config.config import settings


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, param = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer" or not param:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization scheme — expected Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return param


def verify_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """FastAPI dependency that returns the verified token (or raises 401)."""
    token = _extract_bearer(authorization)
    expected = settings.vidiforge_api_token
    if not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


VerifiedToken = Annotated[str, Depends(verify_token)]