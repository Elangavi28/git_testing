from fastapi import FastAPI
from app2.database import model
from app2.database.database import engine
from app2.router import admin,files,users,superadmin,athu,transcript
from app2.database.database import SessionLocal
from app2.router.superadmin import create_superadmin

model.Base.metadata.create_all(bind=engine)
app=FastAPI()


app.include_router(admin.router)
app.include_router(files.router)
app.include_router(users.router)
app.include_router(superadmin.router)
app.include_router(athu.router)
app.include_router(transcript.router)

@app.on_event("startup")
def startup():

    db = SessionLocal()

    try:
        create_superadmin(db)
    finally:
        db.close()