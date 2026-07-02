from pydantic import BaseModel,field_validator,ValidationInfo
from typing import Optional
import re

class UserCreate(BaseModel):
    username:str
    email:str
    password:str
    phone:str
    role:str
    
    @field_validator("username","email","password","phone","role")
    @classmethod
    def validate_not_empty(cls,value,info: ValidationInfo):
        if isinstance(value, str) and not value.strip() or value.lower() == "string":
            raise ValueError(f"{info.field_name} Field is required")
        
        if info.field_name == "phone":
            if not re.fullmatch(r"[6-9]\d{9}", value):
                raise ValueError(
                "Phone number must be a valid 10-digit Indian mobile number"
            )
        return value
    
class UserResponse(BaseModel):
    id: int
    usertname:str
    email:str
    password:str
    phone:str
    role:str

    class Config:
        from_attributes = True
    
class FileCreate(BaseModel):
    user_id: int
    
class FileResponse(BaseModel):
    
    filedata: str # Base64 encoded string
    fileType:str
    fileName:str
    user_id: int
    
    class Config:
        from_attributes = True
        
class Login(BaseModel):
    email:str
    password:str
    role:str
    database:str

class updateUser(BaseModel):
    username:Optional[str] = None
    email:Optional[str] = None
    phone:Optional[str] = None
    role:Optional[str] = None

class updateAdmin(BaseModel):
    username:Optional[str] = None
    email:Optional[str] = None
    phone:Optional[str] = None
    role:Optional[str] = None

class Role(BaseModel):
    role:str
    
class updateFile(BaseModel):
    fileType:Optional[str] = None
    fileName:Optional[str] = None
    user_id: Optional[int] = None
    
class SuperAdminLogin(BaseModel):
    email:str
    password:str

class SuperAdminResponse(BaseModel):
    id: int
    email:str
    password:str

    class Config:
        from_attributes = True
        
class AdminCreate(BaseModel):
    username:str
    email:str
    password:str
    phone:str
    role:str    

class AdminResponse(BaseModel):
    id: int
    username:str
    email:str
    password:str
    phone:str
    role:str

    class Config:
        from_attributes = True
        
class adminUpdate(BaseModel):
    username:Optional[str] = None
    email:Optional[str] = None
    phone:Optional[str] = None
    role:Optional[str] = None
    
    