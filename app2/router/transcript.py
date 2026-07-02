from fastapi import APIRouter, UploadFile, File, HTTPException,Depends
from app2.task.transcript_task import process_meeting_audio
import os
from sqlalchemy.orm import Session
from app2.database.database import get_db
from app2.database.model import Meeting
from fastapi import UploadFile, File
from pydub import AudioSegment
import os
import time

router = APIRouter(prefix="/transcript")

@router.post("/upload-audio/{meeting_id}")
async def upload_audio(meeting_id: int, file: UploadFile = File(...)):
    os.makedirs("app2/uploads", exist_ok=True)

    original_path = f"app2/uploads/{file.filename}"

    # Save uploaded file
    with open(original_path, "wb") as f:
        f.write(await file.read())

    file_ext = file.filename.split(".")[-1].lower()

    # Compressed output path
    compressed_path = original_path.rsplit(".", 1)[0] + "_compressed.wav"

    if file_ext == "wav":
        # Already WAV → just compress
        audio = AudioSegment.from_wav(original_path)
    else:
        # Other formats → convert to WAV
        audio = AudioSegment.from_file(original_path)

    # Compress audio (same for both cases)
    audio = (
        audio.set_frame_rate(16000)   # Reduce sample rate
             .set_channels(1)         # Convert to mono
             .set_sample_width(2)     # 16-bit
    )

    # Export compressed WAV
    audio.export(compressed_path, format="wav")

    # Remove original file
    os.remove(original_path)

    time.sleep(1)

    # Run Celery task
    process_meeting_audio.delay(meeting_id, compressed_path)

    return {
        "message": "Audio uploaded and processed successfully."
    }
    

@router.get("/get-transcript/{meeting_id}")
def get_transcript(meeting_id: int, db: Session = Depends(get_db)):

    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {
        "meeting_id": meeting.id,
        "transcribe":meeting.transcribe,
        "transcript": meeting.transcript 
        }