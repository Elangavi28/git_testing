from dotenv import load_dotenv
import os
import bcrypt
from app2.database.model import SuperAdmin  
from fastapi import APIRouter, Depends, HTTPException,Form
from sqlalchemy.orm import Session
from app2.database.database import get_db
from app2.schema.user import SuperAdminLogin,adminUpdate,AdminCreate
from app2.database.model import User
from app2.utils.athu import create_token,refresh_token,access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security import OAuth2PasswordBearer
from app2.Redis.redis_db import redis_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBearer()

router=APIRouter(prefix="/superadmin")

load_dotenv()

name = os.getenv("SUPERADMIN_NAME")
email = os.getenv("SUPERADMIN_EMAIL")
password = os.getenv("SUPERADMIN_PASSWORD")

def create_superadmin(db):
    superadmin = db.query(SuperAdmin).filter(
        SuperAdmin.email == "superadmin@gmail.com"
    ).first()

    if not superadmin:
        email = os.getenv("SUPERADMIN_EMAIL")
        password = os.getenv("SUPERADMIN_PASSWORD")

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")
        
        new_superadmin = SuperAdmin(
            email=email,
            password=hashed_password
        )

        db.add(new_superadmin)
        db.commit()

        return {
            "message": "Super Admin Created"
            } 
        
# only for admin to update the superadmin details

@router.post('/superadminLogin')
def superadmin(login: SuperAdminLogin=Form(...), db: Session = Depends(get_db)):
    
    superadmin = db.query(SuperAdmin).filter(
        SuperAdmin.email == login.email
    ).first()

    if not superadmin:
        raise HTTPException(
            status_code=404,
            detail="Super Admin not found"
        )
        
    is_valid = bcrypt.checkpw(
        login.password.encode("utf-8"),
        superadmin.password.encode("utf-8")
    )

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Wrong password"
        )
    token_data = {
        "user_id": superadmin.id,
        "email": superadmin.email,
        }

    token = create_token(token_data)
    refresh = refresh_token(token_data)
    
    return {
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "message": "Super Admin login success"
    }
    
@router.post("/create-admin")
def create_admin(
    admin_data: AdminCreate = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = access_token(token)
    
    if payload is None:
        raise HTTPException(
        status_code=401,
        detail="Invalid token"
    )
    existing = db.query(User).filter(User.email == admin_data.email).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    hashed_password = bcrypt.hashpw(admin_data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    new_admin = User(
        username=admin_data.username,
        email=admin_data.email,
        password=hashed_password,
        phone=admin_data.phone,
        role="admin"
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {
        "message": "Admin created successfully",
        "admin": {
            "id": new_admin.id,
            "username": new_admin.username,
            "email": new_admin.email,
            "phone": new_admin.phone,
            "role": new_admin.role
        }
    }
    
@router.get("/alldetails")
def alldata(credentials: HTTPAuthorizationCredentials = Depends(security),db: Session = Depends(get_db)):
    
    token = credentials.credentials
    payload = access_token(token)
    
    if payload is None:
        raise HTTPException(
        status_code=401,
        detail="Invalid token"
    )

    data = db.query(User).all()
    
    users_list = []
    for user in data:
        users_list.append({
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": user.role
        })
        
    return {
        "message": "All details",
        "users": users_list
    }
    
@router.patch("/adminupdate/{id}")
def update_admin(id: int, admin_data: adminUpdate = Form(...), credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):

    token = credentials.credentials
    payload = access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    admin_db = db.query(User).filter(
        User.id == id,
        User.role == "admin"
    ).first()

    if not admin_db:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )

    update_data = admin_data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
            setattr(admin_db, key, value)
    
    db.commit()
    db.refresh(admin_db)

    return {
        "message": "Admin updated successfully",
        "data": {
            "id": admin_db.id,
            "username": admin_db.username,
            "email": admin_db.email,
            "phone": admin_db.phone,
            "role": admin_db.role
        }
    }
    
@router.delete("/admin/{admin_id}")
def delete_admin(
    admin_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    admin = db.query(User).filter(
        User.id == admin_id,
        User.role == "admin"
    ).first()

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )

    db.delete(admin)
    db.commit()

    return {
        "message": "Admin deleted successfully"
    }