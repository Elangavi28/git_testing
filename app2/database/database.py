from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# database connection
DATABASE_URL = "mysql+pymysql://root:Elangavi2819@localhost:3306/cts"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
