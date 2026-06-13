"""
Task domain service.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:

    @staticmethod
    def _is_admin_or_creator(user: User) -> bool:
        return "admin" in user.roles or "task_creator" in user.roles

    @staticmethod
    def create_task(db: Session, payload: TaskCreate, owner_id: str) -> Task:
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        task = Task(**payload.model_dump(), owner_id=owner_id)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task_by_id(db: Session, task_id: str) -> Task:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        return task

    @staticmethod
    def list_tasks(
        db: Session,
        project_id: str | None = None,
        assignee_id: str | None = None,
    ) -> list[Task]:
        q = db.query(Task)
        if project_id:
            q = q.filter(Task.project_id == project_id)
        if assignee_id:
            q = q.filter(Task.assignee_id == assignee_id)
        return q.order_by(Task.created_at.desc()).all()

    @staticmethod
    def update_task(db: Session, task_id: str, payload: TaskUpdate) -> Task:
        task = TaskService.get_task_by_id(db, task_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def complete_task(db: Session, task_id: str, current_user: User) -> Task:
        task = TaskService.set_task_status(db, task_id, TaskStatus.COMPLETED, current_user)
        return task

    @staticmethod
    def set_task_status(db: Session, task_id: str, new_status: TaskStatus, current_user: User) -> Task:
        task = TaskService.get_task_by_id(db, task_id)
        if not TaskService._is_admin_or_creator(current_user) and task.assignee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update status for tasks assigned to you.",
            )
        task.status = new_status
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def assign_task(db: Session, task_id: str, assignee_id: str) -> Task:
        task = TaskService.get_task_by_id(db, task_id)
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee user not found.")
        task.assignee_id = assignee_id
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: str) -> None:
        task = TaskService.get_task_by_id(db, task_id)
        db.delete(task)
        db.commit()