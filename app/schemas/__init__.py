"""
schemas/__init__.py
═══════════════════
Central export point for all Pydantic schemas.

Import from here in routers and services for clean, consistent imports:

    from app.schemas import UserResponse, TaskCreate, ProjectResponse
    from app.schemas.user import TokenResponse
"""

# ── User & Role schemas ──────────────────────────────────────
from app.schemas.user import (
    # Role
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    # User
    UserBase,
    UserCreate,
    UserUpdate,
    UserBriefResponse,
    UserResponse,
    UserWithRolesResponse,
    ChangePasswordRequest,
    # Role assignment
    AssignRoleRequest,
    RemoveRoleRequest,
    # Authentication
    LoginRequest,
    TokenResponse,
    TokenPayload,
    # Pagination
    PaginatedUsersResponse,
)

# ── Project schemas ──────────────────────────────────────────
from app.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectSummaryResponse,
    ProjectDetailResponse,
    ProjectStatusSummary,
    PaginatedProjectsResponse,
)

# ── Task schemas ─────────────────────────────────────────────
from app.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskComplete,
    TaskStatusUpdate,
    TaskAssignRequest,
    TaskResponse,
    TaskDetailResponse,
    TaskFilterParams,
    BulkTaskStatusUpdate,
    BulkTaskAssign,
    BulkOperationResponse,
    PaginatedTasksResponse,
)

__all__ = [
    # Role
    "RoleBase", "RoleCreate", "RoleUpdate", "RoleResponse",
    # User
    "UserBase", "UserCreate", "UserUpdate",
    "UserBriefResponse", "UserResponse", "UserWithRolesResponse",
    "ChangePasswordRequest", "AssignRoleRequest", "RemoveRoleRequest",
    "LoginRequest", "TokenResponse", "TokenPayload",
    "PaginatedUsersResponse",
    # Project
    "ProjectBase", "ProjectCreate", "ProjectUpdate",
    "ProjectResponse", "ProjectSummaryResponse", "ProjectDetailResponse",
    "ProjectStatusSummary", "PaginatedProjectsResponse",
    # Task
    "TaskBase", "TaskCreate", "TaskUpdate", "TaskComplete",
    "TaskStatusUpdate", "TaskAssignRequest",
    "TaskResponse", "TaskDetailResponse",
    "TaskFilterParams",
    "BulkTaskStatusUpdate", "BulkTaskAssign", "BulkOperationResponse",
    "PaginatedTasksResponse",
]
