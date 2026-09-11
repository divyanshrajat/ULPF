from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import create_access_token, verify_password
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import User
import secrets

router = APIRouter()

@router.post("/auth/login", summary="Login to get JWT token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = create_access_token(form_data.username, user.role, user.tenant_id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role
    }
