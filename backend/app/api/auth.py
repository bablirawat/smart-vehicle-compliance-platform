from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.users import User
from app.schemas.auth import LoginRequest, Token, UserOut
from app.auth.passwords import verify_password
from app.auth.jwt import create_access_token
from app.auth.rbac import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    clean_email = payload.email.strip().lower() if payload.email else ""
    user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
        "site_id": user.site_id
    }
    access_token = create_access_token(data=token_data)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value,
        user_id=user.id,
        full_name=user.full_name,
        site_id=user.site_id
    )

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
