import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_user
from app.auth.security import create_access_token, get_password_hash, verify_password
from app.database.connection import get_db
from app.models.user import User
from app.schemas import (
    PasswordResetConfirm,
    PasswordResetRequest,
    PreferencesUpdate,
    TokenResponse,
    UserRegister,
)
from app.services.seed_service import seed_database

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == data.email) | (User.username == data.username)).first():
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=_user_dict(user))


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=_user_dict(user))


@router.get("/me")
def me(user: User = Depends(require_user)):
    return _user_dict(user)


@router.patch("/preferences")
def update_preferences(data: PreferencesUpdate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if data.preferred_language:
        user.preferred_language = data.preferred_language
    if data.preferred_theme:
        user.preferred_theme = data.preferred_theme
    db.commit()
    return _user_dict(user)


@router.post("/password-reset-request")
def password_reset_request(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        user.reset_token = secrets.token_urlsafe(32)
        db.commit()
        return {
            "message": "If email exists, reset link was sent",
            "reset_path": f"/reset-password?token={user.reset_token}",
        }
    return {"message": "If email exists, reset link was sent"}


@router.post("/password-reset-confirm")
def password_reset_confirm(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == data.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None
    db.commit()
    return {"message": "Password updated"}


@router.post("/init-demo")
def init_demo(db: Session = Depends(get_db)):
    seed_database(db)
    return {"message": "Demo data seeded"}


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "preferred_language": user.preferred_language,
        "preferred_theme": user.preferred_theme,
    }
