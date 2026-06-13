"""
Task Tracker API — application entry point.
Serves both the FastAPI backend and the compiled React frontend.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.routers import auth, users, roles, projects, tasks
from app.models import User, Role, UserRole, RefreshSession  # noqa: F401
from app.core.security import hash_password

# Create all tables
Base.metadata.create_all(bind=engine)


def migrate_refresh_sessions_schema() -> None:
    """Apply lightweight runtime schema updates for SQLite deployments."""
    with engine.begin() as conn:
        columns = conn.execute(text("PRAGMA table_info(refresh_sessions)")).fetchall()
        if columns:
            column_names = {col[1] for col in columns}
            if "ip_address" not in column_names:
                conn.execute(text("ALTER TABLE refresh_sessions ADD COLUMN ip_address VARCHAR(45)"))


def seed_database() -> None:
    """Seed default roles and admin user on first startup."""
    db = SessionLocal()
    try:
        default_roles = [
            ("admin",        "Full access to all resources including user/role management"),
            ("task_creator", "Can create and manage projects and tasks"),
            ("viewer",       "Read-only access; may mark assigned tasks as completed"),
        ]
        role_objects: dict[str, Role] = {}
        for role_name, role_desc in default_roles:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=role_desc)
                db.add(role)
                try:
                    db.flush()
                except Exception:
                    # Another worker may have created the role — refresh from DB
                    db.rollback()
                    role = db.query(Role).filter(Role.name == role_name).first()
            role_objects[role_name] = role

        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@tasktracker.app",
                full_name="System Administrator",
                hashed_password=hash_password("admin123"),
            )
            db.add(admin)
            db.flush()
            db.add(UserRole(user_id=admin.id, role_id=role_objects["admin"].id))

        db.commit()
    except Exception as e:
        db.rollback()
        # Suppress errors — another worker may have already seeded
        pass
    finally:
        db.close()


seed_database()
migrate_refresh_sessions_schema()

# ── FastAPI app ───────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Task Tracker REST API with JWT auth and RBAC.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(auth.router,     prefix=API_PREFIX)
app.include_router(users.router,    prefix=API_PREFIX)
app.include_router(roles.router,    prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(tasks.router,    prefix=API_PREFIX)

# ── Health check ──────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

# ── Serve React frontend ──────────────────────────────────────
# In Docker the compiled React dist/ is copied to /app/frontend/
# In local dev, run `npm run dev` in the frontend/ folder instead.
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.isdir(frontend_path) and os.path.isfile(os.path.join(frontend_path, "index.html")):
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    # Catch-all: serve index.html for all non-API routes (React Router)
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_react(full_path: str):
        index = os.path.join(frontend_path, "index.html")
        return FileResponse(index)