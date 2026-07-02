from fastapi import APIRouter, Depends, HTTPException,Form
from fastapi.security import OAuth2PasswordBearer, HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app2.database.database import get_db
from app2.database.model import User
from app2.utils.athu import create_reset_token,verify_reset_token,hash_password
from app2.task.email_tasks import send_reset_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBearer()

router=APIRouter(prefix="/password_reset")

@router.post("/forgot-password")
def forgot_password(email: str=Form(...), db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    token = create_reset_token(user.email)

    send_reset_email.delay(user.email, token)

    return {
        "message": "Reset password link sent",
        "token":token
    }

@router.post("/reset-password")
def reset_password(new_password: str=Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):

    token = credentials.credentials
    
    try:
        email = verify_reset_token(token)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.password = hash_password(new_password)

    db.commit()

    return {
        "message": "Password reset successful"
    }