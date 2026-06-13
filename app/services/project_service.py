"""
Project domain service.
Handles all project CRUD logic independently from the HTTP layer.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """CRUD operations for projects."""

    @staticmethod
    def create_project(db: Session, payload: ProjectCreate, owner_id: str) -> Project:
        project = Project(**payload.model_dump(), owner_id=owner_id)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project_by_id(db: Session, project_id: str) -> Project:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        return project

    @staticmethod
    def list_projects(db: Session) -> list[Project]:
        return db.query(Project).order_by(Project.created_at.desc()).all()

    @staticmethod
    def update_project(db: Session, project_id: str, payload: ProjectUpdate) -> Project:
        project = ProjectService.get_project_by_id(db, project_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str) -> None:
        project = ProjectService.get_project_by_id(db, project_id)
        db.delete(project)
        db.commit()
