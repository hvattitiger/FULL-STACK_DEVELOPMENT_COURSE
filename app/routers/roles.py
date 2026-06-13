"""Roles router — CRUD for application roles (admin only)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import RoleCreate, RoleResponse
from app.services.auth_service import require_roles
from app.services.user_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/", response_model=list[RoleResponse], summary="List all roles")
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    return RoleService.list_roles(db)


@router.post("/", response_model=RoleResponse, status_code=201, summary="Create a new role (admin only)")
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    return RoleService.create_role(db, payload.name, payload.description)


@router.delete("/{role_id}", status_code=204, summary="Delete a role (admin only)")
def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    RoleService.delete_role(db, role_id)
