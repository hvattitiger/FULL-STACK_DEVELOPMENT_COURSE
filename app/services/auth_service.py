"""
Authentication service: dependency injection helpers for extracting
the current user from a JWT bearer token and enforcing role permissions.
Follows Dependency Inversion Principle — routers depend on these abstractions.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that validates the JWT token and returns the active user.
    Raises 401 if the token is missing, invalid, or expired.
    Raises 403 if the user account is inactive.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has no subject.")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled.")
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory that enforces role-based access control.

    Usage::

        @router.post("/resource")
        def create(current_user = Depends(require_roles("admin", "task_creator"))):
            ...
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        user_roles = set(current_user.roles)
        if not user_roles.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of the following roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return _check
