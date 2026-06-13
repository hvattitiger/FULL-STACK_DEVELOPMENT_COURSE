"""Authentication router — login, register, refresh and logout endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_refresh_token
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@router.post("/login", response_model=TokenResponse, summary="Obtain a JWT access token")
def login(payload: LoginRequest, http_request: Request, response: Response, db: Session = Depends(get_db)):
    """Authenticate with username and password. Returns a bearer token valid for 24 hours."""
    client_ip = _get_client_ip(http_request)
    token_bundle = UserService.authenticate(db, payload, client_ip=client_ip)
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=token_bundle["refresh_token"],
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return {
        "access_token": token_bundle["access_token"],
        "token_type": token_bundle["token_type"],
        "user": token_bundle["user"],
    }


@router.post("/refresh", response_model=TokenResponse, summary="Issue a new access token from refresh cookie")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token_value = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token.")

    # Validate session, detect reuse, and rotate tokens
    client_ip = _get_client_ip(request)
    access_token, new_refresh_token = UserService.validate_and_rotate_refresh_session(
        db, refresh_token_value, client_ip=client_ip
    )
    
    # Decode to get user info for response
    payload = decode_refresh_token(refresh_token_value)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    from app.models.user import User
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    # Set new refresh cookie
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=new_refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout", status_code=204, summary="Clear refresh token cookie and revoke session")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token_value = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    
    if refresh_token_value:
        payload = decode_refresh_token(refresh_token_value)
        if payload:
            user_id = payload.get("sub")
            jti = payload.get("jti")
            if user_id:
                # Revoke this specific session
                UserService.revoke_refresh_session(db, user_id, jti)
    
    # Clear cookie
    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path="/",
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/register", response_model=UserResponse, status_code=201, summary="Register a new user")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account. Roles must be assigned by an admin."""
    return UserService.create_user(db, payload)
