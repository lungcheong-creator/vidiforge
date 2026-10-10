"""Bearer token verification.

Accepts the token either as an ``Authorization: Bearer …`` header (used by the
fetch client) or as a ``?token=…`` query parameter. The latter exists because
``<video>`` and ``<a download>`` elements cannot set request headers.
"""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security.utils import get_authorization_scheme_param

from app.config.config import settings

_UNAUTHORIZED = {"WWW-Authenticate": "Bearer"}


def _check(candidate: str) -> str:
    expected = settings.vidiforge_api_token
    if not hmac.compare_digest(candidate, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers=_UNAUTHORIZED,
        )
    return candidate


def verify_token(
    authorization: Annotated[str | None, Header()] = None,
    token: Annotated[str | None, Query(include_in_schema=False)] = None,
) -> str:
    """Return the verified token, or raise 401."""
    if authorization:
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() == "bearer" and param:
            return _check(param)

    if token:
        return _check(token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing credentials — send an Authorization header or ?token=",
        headers=_UNAUTHORIZED,
    )


VerifiedToken = Annotated[str, Depends(verify_token)]
