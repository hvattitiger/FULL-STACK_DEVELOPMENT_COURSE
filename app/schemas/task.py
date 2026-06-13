"""
schemas/task.py
═══════════════
Pydantic v2 schemas for the Task resource.

Schema hierarchy:
  TaskBase → TaskCreate | TaskUpdate | TaskComplete → TaskResponse
                                                    → TaskDetailResponse (with nested project + users)
  Misc: TaskAssignRequest, TaskStatusUpdate, TaskFilterParams, PaginatedTasksResponse
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.task import TaskStatus


# ──────────────────────────────────────────────────────────────
# Base
# ──────────────────────────────────────────────────────────────

class TaskBase(BaseModel):
    """
    Core fields shared across task create and response schemas.
    """
    title: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Short, descriptive title for the task.",
        examples=["Design login page mockup", "Fix null pointer in PaymentService"],
    )
    description: Optional[str] = Field(
        None,
        max_length=5000,
        description="Detailed description, acceptance criteria, or notes for the task.",
    )
    due_date: Optional[date] = Field(
        None,
        description="Deadline for completing this task (ISO 8601: YYYY-MM-DD).",
        examples=["2025-03-31"],
    )
    status: TaskStatus = Field(
        default=TaskStatus.NEW,
        description=(
            "Current lifecycle status of the task. "
            "Allowed values: new | not_started | in_progress | blocked | completed"
        ),
        examples=["new", "in_progress", "completed"],
    )
    project_id: str = Field(
        ...,
        description="UUID of the project this task belongs to.",
    )


# ──────────────────────────────────────────────────────────────
# Request Schemas
# ──────────────────────────────────────────────────────────────

class TaskCreate(TaskBase):
    """
    Request body for creating a new task.
    The task owner is automatically set to the authenticated user.
    Requires role: admin or task_creator.

    Example payload::

        {
            "title": "Design homepage",
            "description": "Create wireframes and Figma designs",
            "due_date": "2025-04-15",
            "status": "new",
            "project_id": "b3f2c...",
            "assignee_id": "a1d4e..."
        }
    """
    assignee_id: Optional[str] = Field(
        None,
        description="UUID of the user to assign this task to. Can be changed later.",
    )


class TaskUpdate(BaseModel):
    """
    Request body for partially updating a task (PATCH semantics).
    All fields are optional — only provided fields are updated.
    Requires role: admin or task_creator.

    Note: viewers use TaskComplete instead of this schema.
    """
    title: Optional[str] = Field(None, min_length=2, max_length=200, description="Updated task title.")
    description: Optional[str] = Field(None, max_length=5000, description="Updated description.")
    due_date: Optional[date] = Field(None, description="Updated deadline.")
    status: Optional[TaskStatus] = Field(
        None,
        description="New status value. Any transition is permitted for admin/task_creator.",
    )
    assignee_id: Optional[str] = Field(
        None,
        description="UUID of the new assignee. Pass null/empty to unassign.",
    )
    project_id: Optional[str] = Field(
        None,
        description="Move this task to a different project by providing the new project UUID.",
    )


class TaskComplete(BaseModel):
    """
    Restricted update schema for the 'viewer' role.
    Viewers may only mark their assigned task as completed.
    They cannot change any other field.

    Used by: POST /tasks/{id}/complete
    """
    status: TaskStatus = Field(
        default=TaskStatus.COMPLETED,
        description="Must be 'completed'. This is the only value accepted from viewers.",
    )

    @model_validator(mode="after")
    def status_must_be_completed(self) -> "TaskComplete":
        """Viewers can only set status to completed — no other transition allowed."""
        if self.status != TaskStatus.COMPLETED:
            raise ValueError("Viewers may only set status to 'completed'.")
        return self


class TaskStatusUpdate(BaseModel):
    """
    Standalone schema for updating only the status of a task.
    Used by admin/task_creator for quick status changes.
    """
    status: TaskStatus = Field(
        ...,
        description="New task status.",
        examples=["in_progress", "blocked", "completed"],
    )


class TaskAssignRequest(BaseModel):
    """
    Request body for assigning or re-assigning a task to a user.
    Used by: POST /tasks/{id}/assign
    """
    assignee_id: str = Field(
        ...,
        description="UUID of the user to assign this task to.",
    )


# ──────────────────────────────────────────────────────────────
# Response Schemas
# ──────────────────────────────────────────────────────────────

class TaskResponse(TaskBase):
    """
    Standard task response returned from list and basic detail endpoints.
    Includes system fields: id, owner_id, assignee_id, timestamps.
    """
    id: str = Field(..., description="UUID of the task.")
    owner_id: Optional[str] = Field(
        None,
        description="UUID of the user who created this task.",
    )
    assignee_id: Optional[str] = Field(
        None,
        description="UUID of the user this task is assigned to. Null if unassigned.",
    )
    created_at: datetime = Field(..., description="Task creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).")

    model_config = {"from_attributes": True}


class TaskDetailResponse(TaskResponse):
    """
    Extended task response that includes denormalized owner and assignee
    usernames for display purposes — avoids extra API calls on the client side.
    Returned by GET /tasks/{id}.
    """
    owner_username: Optional[str] = Field(
        None,
        description="Username of the task creator (denormalized).",
    )
    assignee_username: Optional[str] = Field(
        None,
        description="Username of the assignee (denormalized). Null if unassigned.",
    )
    project_name: Optional[str] = Field(
        None,
        description="Name of the parent project (denormalized).",
    )

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────
# Filter / Query Schemas
# ──────────────────────────────────────────────────────────────

class TaskFilterParams(BaseModel):
    """
    Query parameter schema for filtering the task list.
    Used by GET /tasks/?project_id=...&status=...&assignee_id=...

    All filters are optional and combinable.
    """
    project_id: Optional[str] = Field(
        None,
        description="Filter tasks by project UUID.",
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="Filter tasks by status.",
        examples=["in_progress", "blocked"],
    )
    assignee_id: Optional[str] = Field(
        None,
        description="Filter tasks assigned to a specific user UUID.",
    )
    owner_id: Optional[str] = Field(
        None,
        description="Filter tasks created by a specific user UUID.",
    )
    due_before: Optional[date] = Field(
        None,
        description="Return only tasks with a due_date on or before this date.",
    )
    due_after: Optional[date] = Field(
        None,
        description="Return only tasks with a due_date on or after this date.",
    )

    @model_validator(mode="after")
    def validate_due_range(self) -> "TaskFilterParams":
        if self.due_before and self.due_after and self.due_before < self.due_after:
            raise ValueError("due_before must be >= due_after when both are specified.")
        return self


# ──────────────────────────────────────────────────────────────
# Bulk Operations
# ──────────────────────────────────────────────────────────────

class BulkTaskStatusUpdate(BaseModel):
    """
    Request body for updating the status of multiple tasks at once.
    Requires role: admin.

    Example::

        {
            "task_ids": ["uuid-1", "uuid-2", "uuid-3"],
            "status": "completed"
        }
    """
    task_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of task UUIDs to update.",
    )
    status: TaskStatus = Field(
        ...,
        description="New status to apply to all listed tasks.",
    )


class BulkTaskAssign(BaseModel):
    """
    Request body for assigning multiple tasks to the same user at once.
    Requires role: admin or task_creator.
    """
    task_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of task UUIDs to reassign.",
    )
    assignee_id: str = Field(
        ...,
        description="UUID of the user to assign all listed tasks to.",
    )


class BulkOperationResponse(BaseModel):
    """Response returned after a bulk operation."""
    updated_count: int = Field(..., description="Number of tasks successfully updated.")
    failed_ids: list[str] = Field(
        default=[],
        description="Task UUIDs that could not be updated (not found or permission denied).",
    )


# ──────────────────────────────────────────────────────────────
# Pagination
# ──────────────────────────────────────────────────────────────

class PaginatedTasksResponse(BaseModel):
    """Paginated list of tasks (for future pagination support)."""
    total: int = Field(..., description="Total number of tasks matching the filters.")
    page: int = Field(..., description="Current page number (1-based).")
    page_size: int = Field(..., description="Number of items per page.")
    items: list[TaskResponse] = Field(..., description="Tasks on the current page.")
