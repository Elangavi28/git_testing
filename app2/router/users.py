from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app2.database.database import get_db
from app2.database.model import User,FileCreate,Meeting
from app2.utils.athu import access_token, create_token, refresh_token
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from app2.schema.user import updateUser
from fastapi import Form
import bcrypt
from app2.Redis.redis_db import redis_client
import json

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBearer()

router=APIRouter(prefix="/user_access")

@router.post("/register")
def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(status_code=401, detail="Email is already register")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = User(
        username=username,
        email=email,
        password=hashed_password.decode('utf-8'),
        phone=phone,
        role=role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registration successfully", "user_id": new_user.id}


@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.role != role:
        raise HTTPException(status_code=403, detail="Role mismatch")
        
    is_valid = bcrypt.checkpw(
        password.encode("utf-8"),
        user.password.encode("utf-8")
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Wrong password")
        
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }
    
    token = create_token(token_data)
    refresh = refresh_token(token_data)
    
    return {
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "message": "Login successful"
    }


@router.get("/users_id")
def user_id(id: int, credentials: HTTPAuthorizationCredentials = Depends(security),db:Session=Depends(get_db)):
    
    token = credentials.credentials
    payload=access_token(token)
    if payload is None:
        raise HTTPException(
        status_code=401,
        detail="Invalid token"
    )
    # user_id=payload.get("user_id")
    user=db.query(User).filter(User.id==id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return{
        "id":user.id,
        "username":user.username,
        "email":user.email,
        "phone":user.phone,
        "role":user.role
    }
    
@router.get("/users")
def get_users(credentials: HTTPAuthorizationCredentials = Depends(security),db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = access_token(token)
    
    if payload is None:
        raise HTTPException(
        status_code=401,
        detail="Invalid token"
    )

    users = db.query(User).filter(User.role == "user").all()

    result = []

    for user in users:
        user_files = db.query(FileCreate).filter(
            FileCreate.user_id == user.id
        ).all()

        user_data = {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": user.role
        }

        # Add files only if files exist
        if user_files:
            user_data["files"] = [
                {
                    "id": file.id,
                    "filename": file.fileName,
                    "filetype": file.fileType,
                }
                for file in user_files
            ]

        result.append(user_data)

    return result    
    
@router.patch("/userupdate/{id}")
def update_user(id: int,data:updateUser=Form(...), credentials: HTTPAuthorizationCredentials = Depends(security),db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(user, key, value)
        
    db.commit()
    db.refresh(user)

    return {
        "message": "User updated successfully",
        "data": {
            "username": user.username,
            "email": user.email,
            "phone":user.phone,
            "role":user.role,
        }
    }

@router.delete("/userdelete/{id}")
def user_del(id:int,credentials: HTTPAuthorizationCredentials = Depends(security),db:Session=Depends(get_db)):
    
    token = credentials.credentials
    payload = access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return{
        "message": "User deleted successfully"
    }

@router.delete("/deleteall")
def delete_All(db:Session=Depends(get_db)):
    db.query(User).delete()
    db.commit()
    
    return{
        "Message":"All User deleted successfully"
    }


@router.get("/get-meeting/{user_id}")
def get_meeting(user_id: int, db: Session = Depends(get_db)):

    redis_key = f"meet:{user_id}"

    # Check Redis
    meeting_data = redis_client.get(redis_key)

    if meeting_data:
        return {
            "source": "Redis Cache",
            "data": json.loads(meeting_data)
        }

    # Check MySQL
    meeting = db.query(Meeting).filter(Meeting.user_id == user_id).first()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    data = {
        "admin_id": meeting.admin_id,
        "user_id": meeting.user_id,
        "meet_link": meeting.meet_link
    }

    # Store in Redis
    redis_client.set(
        redis_key,
        json.dumps(data)
    )

    return {
        "source": "Database",
        "data": data
    }