from sqlalchemy import Column, Integer, String,ForeignKey,JSON
from sqlalchemy.dialects.mysql import LONGTEXT
from app2.database.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "user"
    
    id=Column(Integer,primary_key=True,index=True,autoincrement=True)
    username = Column(String(100),nullable=False)
    email = Column(String(100), unique=True,nullable=False)
    password = Column(String(255),nullable=False)
    phone=Column(String(100),nullable=False)
    role=Column(String(500),nullable=False)
    
    file =relationship("FileCreate", back_populates="user",cascade="all, delete")
    meeting = relationship("Meeting", back_populates="users")
    
class FileCreate(Base):
    
    __tablename__ = "file"
    
    id=Column(Integer,primary_key=True,index=True,autoincrement=True)
    filedata = Column(LONGTEXT)
    fileName = Column(String(255))
    fileType=Column(String(500))
    user_id= Column(Integer, ForeignKey("user.id"))
    
    user = relationship("User", back_populates="file")
    
    
class SuperAdmin(Base):
    
    __tablename__ = "superadmins"
    
    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    email = Column(String(100), unique=True)
    password = Column(String(255))
    

class Meeting(Base):
    
    __tablename__ = "meetings"
    
    id=Column(Integer, primary_key=True, index=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    admin_id=Column(Integer)
    meet_link =Column(String(500))
    transcribe = Column(LONGTEXT, nullable=True) 
    transcript = Column(JSON, nullable=True)
    
    users = relationship("User", back_populates="meeting")

