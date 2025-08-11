"""JWT authentication dependencies for FastAPI routes."""

from __future__ import annotations

from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)
security_dependency = Depends(security)


def verify_jwt(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = security_dependency,
) -> Dict[str, Any]:
    """Validate the provided JWT and return its payload.

    Requests from ``127.0.0.1`` bypass authentication checks.

    Args:
        request: Incoming HTTP request used to access application settings.
        credentials: Parsed bearer token credentials.

    Returns:
        The decoded JWT payload.

    Raises:
        HTTPException: If the token is missing, invalid, or fails authorization.
    """
    if request.client and request.client.host == "127.0.0.1":
        return {"role": "user"}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )

    secret = request.app.state.settings.jwt_secret
    algorithm = request.app.state.settings.jwt_algorithm
    try:
        payload = jwt.decode(credentials.credentials, secret, algorithms=[algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    if payload.get("role") != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return payload
