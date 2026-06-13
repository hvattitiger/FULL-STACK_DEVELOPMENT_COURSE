"""
Users router.
Provides endpoints for user management and role assignment.
Admin-only except /me and user listing for task creators.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import AssignRoleRequest, UserResponse, UserUpdate
from app.services.auth_service import get_current_user, require_roles
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the authenticated user."""
    return current_user


@router.get("/", response_model=list[UserResponse], summary="List all users (admin/task_creator)")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "task_creator")),
):
    return UserService.list_users(db)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID (admin only)")
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    return UserService.get_user_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user (admin only)")
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    return UserService.update_user(db, user_id, payload)


@router.delete("/{user_id}", status_code=204, summary="Delete user (admin only)")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    UserService.delete_user(db, user_id)


@router.post("/{user_id}/roles", response_model=UserResponse, summary="Assign role to user (admin only)")
def assign_role(
    user_id: str,
    payload: AssignRoleRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    return UserService.assign_role(db, user_id, payload.role_id)


@router.delete("/{user_id}/roles/{role_id}", response_model=UserResponse, summary="Remove role from user (admin only)")
def remove_role(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    return UserService.remove_role(db, user_id, role_id)
