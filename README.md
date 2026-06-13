# Task Tracker — FastAPI Application

A production-ready task management REST API with JWT authentication, role-based access control,
project management, and task assignment capabilities.

---

## Features

| Feature | Details |
|---|---|
| **Authentication** | JWT bearer tokens (24h expiry), bcrypt password hashing |
| **Roles** | `admin`, `task_creator`, `viewer` |
| **Projects** | CRUD with owner, dates, description |
| **Tasks** | CRUD with status, due date, project, assignee |
| **UI** | Self-contained single-file frontend served by FastAPI |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum update SECRET_KEY for production
```

### 3. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Access the application

| URL | Description |
|---|---|
| `http://localhost:8000` | Web UI |
| `http://localhost:8000/api/docs` | Swagger / OpenAPI docs |
| `http://localhost:8000/api/redoc` | ReDoc documentation |

**Default admin credentials:** `admin` / `admin123`

---

## Architecture

```
task_tracker/
├── app/
│   ├── main.py              # App factory, middleware, seeding
│   ├── core/
│   │   ├── config.py        # Pydantic Settings (env vars)
│   │   ├── database.py      # SQLAlchemy engine & session
│   │   └── security.py      # JWT + bcrypt utilities
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py          # User, Role, UserRole
│   │   ├── project.py       # Project
│   │   └── task.py          # Task (with TaskStatus enum)
│   ├── schemas/             # Pydantic request/response models
│   │   ├── user.py
│   │   ├── project.py
│   │   └── task.py
│   ├── services/            # Domain logic (SOLID SRP)
│   │   ├── auth_service.py  # get_current_user, require_roles
│   │   ├── user_service.py  # UserService, RoleService
│   │   ├── project_service.py
│   │   └── task_service.py
│   └── routers/             # FastAPI route handlers
│       ├── auth.py
│       ├── users.py
│       ├── roles.py
│       ├── projects.py
│       └── tasks.py
└── frontend/
    └── index.html           # Self-contained SPA
```

---

## API Endpoints

### Authentication
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Obtain JWT token |
| `POST` | `/api/v1/auth/register` | Register new user |

### Users (admin only)
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/users/me` | Current user profile |
| `GET` | `/api/v1/users/` | List all users |
| `PATCH` | `/api/v1/users/{id}` | Update user |
| `DELETE` | `/api/v1/users/{id}` | Delete user |
| `POST` | `/api/v1/users/{id}/roles` | Assign role |
| `DELETE` | `/api/v1/users/{id}/roles/{role_id}` | Remove role |

### Roles (admin only)
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/roles/` | List roles |
| `POST` | `/api/v1/roles/` | Create role |
| `DELETE` | `/api/v1/roles/{id}` | Delete role |

### Projects
| Method | Path | Access |
|---|---|---|
| `GET` | `/api/v1/projects/` | All authenticated users |
| `POST` | `/api/v1/projects/` | admin, task_creator |
| `PATCH` | `/api/v1/projects/{id}` | admin, task_creator |
| `DELETE` | `/api/v1/projects/{id}` | admin only |

### Tasks
| Method | Path | Access |
|---|---|---|
| `GET` | `/api/v1/tasks/` | All authenticated users |
| `POST` | `/api/v1/tasks/` | admin, task_creator |
| `PATCH` | `/api/v1/tasks/{id}` | admin, task_creator |
| `POST` | `/api/v1/tasks/{id}/complete` | Any user (own tasks only for viewer) |
| `POST` | `/api/v1/tasks/{id}/assign/{user_id}` | admin, task_creator |
| `DELETE` | `/api/v1/tasks/{id}` | admin only |

---

## Role Permissions Summary

| Action | admin | task_creator | viewer |
|---|:---:|:---:|:---:|
| Manage users & roles | ✅ | ❌ | ❌ |
| Create/edit projects | ✅ | ✅ | ❌ |
| Delete projects | ✅ | ❌ | ❌ |
| Create/edit tasks | ✅ | ✅ | ❌ |
| Assign tasks | ✅ | ✅ | ❌ |
| Delete tasks | ✅ | ❌ | ❌ |
| Complete own task | ✅ | ✅ | ✅ |
| View all data | ✅ | ✅ | ✅ |

---

## SOLID Principles Applied

- **S** — Each class/module has one responsibility (`UserService`, `ProjectService`, `TaskService`, routers, models, schemas all separate)
- **O** — Role checks use a factory (`require_roles("admin", "task_creator")`) so new roles don't require modifying existing code
- **L** — Services accept `Session` abstraction rather than concrete implementation details
- **I** — Separate `TaskCreate`, `TaskUpdate`, `TaskComplete` schemas for different use cases
- **D** — Routers depend on service abstractions injected via FastAPI's DI system; `get_db` provides the session

---

## Production Checklist

- [ ] Change `SECRET_KEY` to a cryptographically random value (`openssl rand -hex 32`)
- [ ] Switch `DATABASE_URL` to PostgreSQL
- [ ] Set `DEBUG=false`
- [ ] Change the default admin password
- [ ] Configure `ALLOWED_ORIGINS` to your specific domain
- [ ] Add HTTPS via reverse proxy (nginx/traefik)
