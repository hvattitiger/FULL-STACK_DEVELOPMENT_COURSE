"""
Projects router.
- Admins and task_creators can create/update/delete projects.
- All authenticated users can view projects.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.auth_service import get_current_user, require_roles
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectResponse], summary="List all projects")
def list_projects(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return ProjectService.list_projects(db)


@router.post("/", response_model=ProjectResponse, status_code=201, summary="Create a project")
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "task_creator")),
):
    return ProjectService.create_project(db, payload, current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project details")
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return ProjectService.get_project_by_id(db, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse, summary="Update a project")
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "task_creator")),
):
    return ProjectService.update_project(db, project_id, payload)


@router.delete("/{project_id}", status_code=204, summary="Delete a project (admin only)")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    ProjectService.delete_project(db, project_id)
