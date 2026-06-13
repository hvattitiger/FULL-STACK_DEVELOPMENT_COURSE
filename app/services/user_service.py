"""
User domain service.
Encapsulates all business logic for users, roles, and refresh sessions.
Keeps routers thin and testable.
"""
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_refresh_token
from app.models.user import Role, User, UserRole, RefreshSession
from app.schemas.user import UserCreate, UserUpdate, LoginRequest
from app.core.config import settings


class UserService:
    """CRUD and authentication operations for users."""

    # ------------------------------------------------------------------ #
    # Authentication                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def authenticate(db: Session, request: LoginRequest, client_ip: Optional[str] = None) -> dict:
        """
        Validate credentials, create a refresh session, and return access + refresh tokens.
        Raises 401 if credentials are invalid.
        """
        user: Optional[User] = db.query(User).filter(User.username == request.username).first()
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password.",
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled.")

        # Enforce one active device/session per user.
        db.query(RefreshSession).filter(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked == False,
        ).update({"revoked": True}, synchronize_session=False)

        access_token = create_access_token(subject=user.id)
        refresh_token, jti = create_refresh_token(subject=user.id)
        
        # Store refresh session in database
        session_expires = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        refresh_session = RefreshSession(
            user_id=user.id,
            refresh_token_jti=jti,
            ip_address=client_ip,
            expires_at=session_expires,
        )
        db.add(refresh_session)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    @staticmethod
    def validate_and_rotate_refresh_session(db: Session, refresh_token: str, client_ip: Optional[str] = None) -> tuple[str, str]:
        """
        Validate refresh token, check session state, and rotate the token.
        
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            401 if token is invalid, expired, revoked, or reused.
        """
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if not user_id or not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload.",
            )

        # Fetch user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled.")

        # Fetch session
        session = db.query(RefreshSession).filter(
            RefreshSession.refresh_token_jti == jti,
            RefreshSession.user_id == user_id,
        ).first()
        
        if not session:
            # Token reuse detected — revoke all sessions for this user
            db.query(RefreshSession).filter(RefreshSession.user_id == user_id).update(
                {"revoked": True}, synchronize_session=False
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or reused — all sessions revoked.",
            )
        
        if session.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh session has been revoked.",
            )

        if session.ip_address and client_ip and session.ip_address != client_ip:
            db.query(RefreshSession).filter(
                RefreshSession.user_id == user_id,
            ).update({"revoked": True}, synchronize_session=False)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session IP mismatch detected — all sessions revoked.",
            )
        
        # Ensure expires_at is timezone-aware for comparison
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired.",
            )

        # Mark session as used and generate new tokens
        session.last_used_at = datetime.now(timezone.utc)
        
        access_token = create_access_token(subject=user.id)
        new_refresh_token, new_jti = create_refresh_token(subject=user.id)
        
        # Create new session and revoke old one
        new_session_expires = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        new_session = RefreshSession(
            user_id=user.id,
            refresh_token_jti=new_jti,
            ip_address=client_ip or session.ip_address,
            expires_at=new_session_expires,
        )
        session.revoked = True  # Revoke the old token after one use
        db.add(new_session)
        db.commit()
        
        return access_token, new_refresh_token

    @staticmethod
    def revoke_refresh_session(db: Session, user_id: str, jti: Optional[str] = None) -> None:
        """
        Revoke a specific refresh session (if jti is provided) or all sessions for a user.
        """
        if jti:
            db.query(RefreshSession).filter(
                RefreshSession.user_id == user_id,
                RefreshSession.refresh_token_jti == jti,
            ).update({"revoked": True}, synchronize_session=False)
        else:
            # Revoke all sessions for this user (logout all devices)
            db.query(RefreshSession).filter(
                RefreshSession.user_id == user_id,
            ).update({"revoked": True}, synchronize_session=False)
        db.commit()

    # ------------------------------------------------------------------ #
    # User CRUD                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_user(db: Session, payload: UserCreate) -> User:
        """Create a new user. Raises 409 if username or email already exists."""
        if db.query(User).filter(User.username == payload.username).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken.")
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

        user = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        """Fetch a user by ID or raise 404."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    @staticmethod
    def list_users(db: Session) -> list[User]:
        return db.query(User).all()

    @staticmethod
    def update_user(db: Session, user_id: str, payload: UserUpdate) -> User:
        """Partially update a user's profile."""
        user = UserService.get_user_by_id(db, user_id)
        update_data = payload.model_dump(exclude_unset=True)
        if "password" in update_data:
            user.hashed_password = hash_password(update_data.pop("password"))
        for field, value in update_data.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: str) -> None:
        """Delete a user account."""
        user = UserService.get_user_by_id(db, user_id)
        db.delete(user)
        db.commit()

    # ------------------------------------------------------------------ #
    # Role Management                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def assign_role(db: Session, user_id: str, role_id: str) -> User:
        """Assign a role to a user. No-op if already assigned."""
        user = UserService.get_user_by_id(db, user_id)
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

        already_assigned = db.query(UserRole).filter_by(user_id=user_id, role_id=role_id).first()
        if not already_assigned:
            db.add(UserRole(user_id=user_id, role_id=role_id))
            db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def remove_role(db: Session, user_id: str, role_id: str) -> User:
        """Remove a role from a user."""
        user_role = db.query(UserRole).filter_by(user_id=user_id, role_id=role_id).first()
        if not user_role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found.")
        db.delete(user_role)
        db.commit()
        user = UserService.get_user_by_id(db, user_id)
        return user


class RoleService:
    """CRUD operations for roles."""

    @staticmethod
    def create_role(db: Session, name: str, description: Optional[str]) -> Role:
        if db.query(Role).filter(Role.name == name).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists.")
        role = Role(name=name, description=description)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def list_roles(db: Session) -> list[Role]:
        return db.query(Role).all()

    @staticmethod
    def delete_role(db: Session, role_id: str) -> None:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
        db.delete(role)
        db.commit()
