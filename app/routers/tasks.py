"""
Tasks router.
Role-based access:
  - admin + task_creator: full CRUD, see all tasks
    - viewer: can only see tasks assigned to them, update status on their own tasks
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskStatusUpdate, TaskUpdate
from app.services.auth_service import get_current_user, require_roles
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _is_viewer_only(user: User) -> bool:
    """Returns True if user has no admin or task_creator role."""
    return "admin" not in user.roles and "task_creator" not in user.roles


@router.get("/", response_model=list[TaskResponse], summary="List tasks")
def list_tasks(
    project_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignee_filter = current_user.id if _is_viewer_only(current_user) else None
    return TaskService.list_tasks(db, project_id, assignee_filter)


@router.post("/", response_model=TaskResponse, status_code=201, summary="Create a task")
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "task_creator")),
):
    return TaskService.create_task(db, payload, current_user.id)


@router.get("/{task_id}", response_model=TaskResponse, summary="Get task details")
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException, status
    task = TaskService.get_task_by_id(db, task_id)
    if _is_viewer_only(current_user) and task.assignee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return task


@router.patch("/{task_id}", response_model=TaskResponse, summary="Update a task")
def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "task_creator")),
):
    return TaskService.update_task(db, task_id, payload)


@router.post("/{task_id}/complete", response_model=TaskResponse, summary="Mark task as completed")
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaskService.complete_task(db, task_id, current_user)


@router.patch("/{task_id}/status", response_model=TaskResponse, summary="Update task status")
def update_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaskService.set_task_status(db, task_id, payload.status, current_user)


@router.post("/{task_id}/assign/{assignee_id}", response_model=TaskResponse, summary="Assign task to user")
def assign_task(
    task_id: str,
    assignee_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "task_creator")),
):
    return TaskService.assign_task(db, task_id, assignee_id)


@router.delete("/{task_id}", status_code=204, summary="Delete a task (admin only)")
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    TaskService.delete_task(db, task_id)