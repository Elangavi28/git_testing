from fastapi import APIRouter, Depends,HTTPException,Form,File, UploadFile
from fastapi import Depends,HTTPException
from sqlalchemy.orm import Session
from app2.database.database import get_db
from app2.database.model import User,FileCreate
from app2.schema.user import updateFile
from app2.utils.athu import access_token
from fastapi.security import OAuth2PasswordBearer
from typing import List
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from app2.Redis.redis_db import redis_client
import json
from app2.task.files_task import process_uploaded_file

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBearer()

router=APIRouter(prefix="/file_access")

@router.post("/upload-file/{user_id}")
async def upload_file(
    user_id: int,
    files:List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()    

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    task_ids=[]
    for file in files:
        
        content =await file.read()
        
        # Send file to Celery
        task = process_uploaded_file.delay(content, file.filename, file.content_type, user_id)
        
        task_ids.append({
            "file_name": file.filename,
            "task_id": task.id
        })
    
    return {
        "message": "File stored successfully",
        "files": task_ids
    }
    
@router.get("/file/{file_id}")
def get_file(file_id: int, db: Session = Depends(get_db)):

    redis_key = f"file:{file_id}"

    # Check Redis first
    cached_data = redis_client.get(redis_key)

    if cached_data:
        return {
            "source": "Redis Cache",
            "data": json.loads(cached_data)
        }

    # If not in Redis, check MySQL
    file_data = db.query(FileCreate).filter(FileCreate.id == file_id).first()

    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    # Save back to Redis
    redis_client.set(
        redis_key,
        json.dumps({
            "id": file_data.id,
            "file_name": file_data.fileName,
            "file_type": file_data.fileType,
            "user_id": file_data.user_id
        })
    )

    return {
        "source": "MySQL Database",
        "data": {
            "id": file_data.id,
            "file_name": file_data.fileName,
            "file_type": file_data.fileType,
            "user_id": file_data.user_id
        }
    }
    
@router.get("/files/{user_id}")
def get_files(user_id: int, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):

    token = credentials.credentials
    payload = access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    files = db.query(FileCreate).filter(FileCreate.user_id == user_id).all()
    
    result=[]
    
    for user in files:
        result.append({
            "id": user.id,
            "user_id":user.user_id,
            "type":user.fileType,
            "fileName":user.fileName,
            "filedata": user.filedata
        })
    return result

@router.patch("/file/{id}")
def update_file(id: int,data:updateFile=Form(...), db: Session = Depends(get_db)):

    file = db.query(FileCreate).filter(FileCreate.id == id).first()

    if not file:
        raise HTTPException(status_code=404, detail="file not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(file, key, value)
        
    db.commit()
    db.refresh(file)

    return {
        "message": "File updated successfully",
        "data": {
            "fileName": file.fileName,
            "fileType": file.fileType,
            
        }
    }

@router.delete("/file/{id}")
def file_del(id:int,db:Session=Depends(get_db)):
    
    file = db.query(FileCreate).filter(FileCreate.id == id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    db.delete(file)
    db.commit()
    return{
        "message": "File deleted by user"
    }
    
@router.delete("/deleteallfiles")
def deleteall(db:Session=Depends(get_db)):
    db.query(FileCreate).delete()
    db.commit()
    
    return{
         "Message":"All files deleted successfully"
    }


