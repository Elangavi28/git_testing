from app2.celery_worker import celery_app
from app2.services.meeting import create_google_meet
from app2.database.model import Meeting
from app2.database.database import SessionLocal
from app2.Redis.redis_db import redis_client
import json
import os
import subprocess

@celery_app.task
def create_meet_task(admin_id, user_id):

    db = SessionLocal()

    try:
        # Create Google Meet link
        meet_link = create_google_meet()

        # Save into MySQL
        new_meeting = Meeting(
            admin_id=admin_id,
            user_id=user_id,
            meet_link=meet_link
        )

        db.add(new_meeting)
        db.commit()
        db.refresh(new_meeting)

        # Save into Redis cache
        redis_key = f"meeting:{new_meeting.id}"

        redis_client.set(
            redis_key,
            json.dumps({
                "meeting_id": new_meeting.id,
                "admin_id": admin_id,
                "user_id": user_id,
                "meet_link": meet_link
            })
        )

        return {
            "admin_id": admin_id,
            "user_id": user_id,
            "meet_link": meet_link
        }

    finally:
        db.close()
        
# def convert_to_wav(input_file):
#     output_file = os.path.splitext(input_file)[0] + ".wav"

#     subprocess.run([
#         "ffmpeg",
#         "-i", input_file,
#         output_file
#     ], check=True)

#     return output_file