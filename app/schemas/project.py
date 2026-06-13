"""
schemas/project.py
══════════════════
Pydantic v2 schemas for the Project resource.

Schema hierarchy:
  ProjectBase → ProjectCreate | ProjectUpdate → ProjectResponse
                                              → ProjectDetailResponse (with tasks + owner)
  Misc: ProjectSummaryResponse, ProjectStatusSummary
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ──────────────────────────────────────────────────────────────
# Base
# ──────────────────────────────────────────────────────────────

class ProjectBase(BaseModel):
    """
    Shared fields for project schemas.
    Includes cross-field date validation to ensure end_date >= start_date.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Name of the project. Must be unique within an owner.",
        examples=["Website Redesign", "Q4 Marketing Campaign"],
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed description of the project goals and scope.",
    )
    start_date: Optional[date] = Field(
        None,
        description="Planned start date of the project (ISO 8601 format: YYYY-MM-DD).",
        examples=["2025-01-15"],
    )
    end_date: Optional[date] = Field(
        None,
        description="Planned end/deadline date of the project (ISO 8601 format: YYYY-MM-DD).",
        examples=["2025-06-30"],
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "ProjectBase":
        """Ensure end_date is not before start_date when both are provided."""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError(
                    f"end_date ({self.end_date}) must be on or after start_date ({self.start_date})."
                )
        return self


# ──────────────────────────────────────────────────────────────
# Request Schemas
# ──────────────────────────────────────────────────────────────

class ProjectCreate(ProjectBase):
    """
    Request body for creating a new project.
    The owner is automatically set to the authenticated user.
    Requires role: admin or task_creator.
    """
    pass


class ProjectUpdate(BaseModel):
    """
    Request body for partially updating a project (PATCH semantics).
    All fields are optional — only provided fields will be changed.
    Requires role: admin or task_creator.
    """
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=200,
        description="New project name.",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Updated description.",
    )
    start_date: Optional[date] = Field(None, description="Updated start date.")
    end_date: Optional[date] = Field(None, description="Updated end/deadline date.")

    @model_validator(mode="after")
    def validate_date_range(self) -> "ProjectUpdate":
        """Validate date range only when both dates are present in the update."""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError(
                    f"end_date ({self.end_date}) must be on or after start_date ({self.start_date})."
                )
        return self


# ──────────────────────────────────────────────────────────────
# Response Schemas
# ──────────────────────────────────────────────────────────────

class ProjectResponse(ProjectBase):
    """
    Standard project response returned from list and detail endpoints.
    Includes system-managed fields: id, owner_id, timestamps.
    """
    id: str = Field(..., description="UUID of the project.")
    owner_id: Optional[str] = Field(
        None,
        description="UUID of the user who owns/created this project.",
    )
    created_at: datetime = Field(..., description="Creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).")

    model_config = {"from_attributes": True}


class ProjectSummaryResponse(BaseModel):
    """
    Minimal project representation used when embedding inside task responses
    to avoid circular nesting.
    """
    id: str = Field(..., description="UUID of the project.")
    name: str = Field(..., description="Name of the project.")
    end_date: Optional[date] = Field(None, description="Project deadline.")

    model_config = {"from_attributes": True}


class ProjectDetailResponse(ProjectResponse):
    """
    Extended project response that includes nested task count statistics
    and owner info. Returned by GET /projects/{id}.
    """
    task_count: int = Field(
        default=0,
        description="Total number of tasks in this project.",
    )
    completed_task_count: int = Field(
        default=0,
        description="Number of tasks with status 'completed'.",
    )
    owner_username: Optional[str] = Field(
        None,
        description="Username of the project owner (denormalized for convenience).",
    )

    model_config = {"from_attributes": True}


class ProjectStatusSummary(BaseModel):
    """
    Aggregated task-status breakdown for a project.
    Used by dashboard and reporting endpoints.
    """
    project_id: str = Field(..., description="UUID of the project.")
    project_name: str = Field(..., description="Name of the project.")
    new: int = Field(default=0, description="Tasks with status 'new'.")
    not_started: int = Field(default=0, description="Tasks with status 'not_started'.")
    in_progress: int = Field(default=0, description="Tasks with status 'in_progress'.")
    blocked: int = Field(default=0, description="Tasks with status 'blocked'.")
    completed: int = Field(default=0, description="Tasks with status 'completed'.")
    total: int = Field(default=0, description="Total task count across all statuses.")


# ──────────────────────────────────────────────────────────────
# Pagination
# ──────────────────────────────────────────────────────────────

class PaginatedProjectsResponse(BaseModel):
    """Paginated list of projects (for future pagination support)."""
    total: int = Field(..., description="Total number of projects matching the query.")
    page: int = Field(..., description="Current page number (1-based).")
    page_size: int = Field(..., description="Number of items per page.")
    items: list[ProjectResponse] = Field(..., description="Projects on the current page.")
