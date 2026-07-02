from app2.celery_worker import celery_app
from app2.database.database import SessionLocal
from app2.database.model import FileCreate
import base64
import json
from app2.Redis.redis_db import redis_client


@celery_app.task(bind=True)
def process_uploaded_file(self, file_content, file_name, file_type, user_id):
    
    db = SessionLocal()

    try:
        base64_data = base64.b64encode(file_content).decode("utf-8")[:200]

        new_file = FileCreate(
            filedata=base64_data,
            fileName=file_name,
            fileType=file_type,
            user_id=user_id
        )

        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        redis_key = f"file:{new_file.id}"

        redis_client.set(
            redis_key,
            json.dumps({
                "file_id": new_file.id,
                "file_name": new_file.fileName,
                "file_type": new_file.fileType,
                "user_id": new_file.user_id
            })
        )

        return {
            "id": new_file.id,
            "file_name": new_file.fileName,
            "user_id": new_file.user_id
        }

    finally:
        db.close()