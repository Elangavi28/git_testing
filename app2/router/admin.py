from fastapi import APIRouter, Depends, HTTPException,Form
from sqlalchemy.orm import Session
from app2.database.database import get_db
from app2.database.model import User,FileCreate
from app2.schema.user import updateAdmin
from app2.utils.athu import access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security import OAuth2PasswordBearer
from app2.task.meet_task import create_meet_task

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBearer()
router = APIRouter(prefix="/admin_access")

@router.get('/users')
def admin(credentials: HTTPAuthorizationCredentials = Depends(security), db:Session=Depends(get_db)):
    
    token = credentials.credentials
    payload=access_token(token)
    
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
                    "filedata": file.filedata,
                }
                for file in user_files
            ]

        result.append(user_data)

    return result    

@router.get("/admins")
def get_admins(credentials: HTTPAuthorizationCredentials = Depends(security),db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = access_token(token)
    if payload is None:
        raise HTTPException(
        status_code=401,
        detail="Invalid token"
    )

    admins = db.query(User).filter(
        User.role == "admin"
    ).all()

    return {
        "message": "All admins",
        "admins": [
            {
                "id": admin.id,
                "name": admin.username,
                "email": admin.email,
                "phone": admin.phone,
                "role": admin.role
            }
            for admin in admins
        ]
    }

    
@router.patch("/userupdate/{id}")
def userupdate(id:int,data:updateAdmin=Form(...),credentials: HTTPAuthorizationCredentials = Depends(security),db: Session = Depends(get_db)):
    
    token = credentials.credentials
    payload=access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
        
    admin = db.query(User).filter(User.id == id).first()

    if not admin:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(admin, key, value)
    
    db.commit()
    db.refresh(admin)

    return {
        "message": "updated by admin",
        "data": {
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "phone":admin.phone,
            "role":admin.role,
        }
    }

@router.delete("/userdelete/{id}")
def userdelete(id:int,credentials: HTTPAuthorizationCredentials = Depends(security),db:Session=Depends(get_db)):
    
    token = credentials.credentials
    payload=access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    admin = db.query(User).filter(User.id == id).first()

    if not admin:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(admin)
    db.commit()
    return{
        "message": "deleted by admin"
    }  

@router.delete("/deletefile/{id}")
def deleteFile(id:int,credentials: HTTPAuthorizationCredentials = Depends(security),db:Session=Depends(get_db)):
    
    token = credentials.credentials
    payload=access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    admin = db.query(FileCreate).filter(FileCreate.id == id).first()

    if not admin:
        raise HTTPException(status_code=404, detail="File not found")
    
    db.delete(admin)
    db.commit()
    return{
        "message": "File deleted by admin"
    }  

@router.post("/create-meeting/{admin_id}/{user_id}")
def create_meeting(admin_id: int, user_id: int):

    task = create_meet_task.delay(admin_id, user_id)

    return {
        "message": "Meeting creation started",
        "task_id": task.id
    }