from app2.celery_worker import celery_app
from app2.database.database import SessionLocal
from app2.database.model import Meeting
from app2.services.transcript_service import process_audio
import ollama
from langchain_ollama import ChatOllama
import json



llm = ChatOllama(
    model="llama3",
    temperature=0
)

def detect_speaker_roles(transcript_data):
    transcript_text = "\n".join(
        [f'{item["speaker"]}: {item["text"]}' for item in transcript_data]
    )

    # First speaker info
    first_speaker = transcript_data[0]["speaker"] if transcript_data else None

    prompt = f"""
Analyze this transcript and return ONLY valid JSON.

Tasks:
1. Detect the conversation type automatically.
2. Assign meaningful roles to every speaker.
3. Never keep names like SPEAKER_00, SPEAKER_01, etc.

Role Detection Rules:
- The speaker who starts the conversation is often HR or Moderator.
- The speaker asking the most questions is likely HR or Moderator.
- The speaker controlling flow like:
  "next", "what do you think", "please continue", "let's start"
  is usually Moderator/HR.
- Speakers mainly responding are Candidates/Participants.

Conversation Types:
- Interview:
    HR, Candidate 1, Candidate 2
- Group Discussion:
    Moderator, Candidate 1, Candidate 2, Candidate 3
- Meeting:
    Manager, Employee 1, Employee 2
- Family:
    Father, Mother, Son, Daughter
- Casual:
    Friend 1, Friend 2

Important:
- First speaker is: {first_speaker}
- Use this as a strong clue.

Return format example:
{{
    "conversation_type": "Group Discussion",
    "speakers": {{
        "SPEAKER_00": "Moderator",
        "SPEAKER_01": "Candidate 1",
        "SPEAKER_02": "Candidate 2"
    }}
}}

Transcript:
{transcript_text}
"""

    response = llm.invoke(prompt)

    try:
        cleaned = response.content.strip()
        cleaned = cleaned.replace("```json", "").replace("```", "")

        result = json.loads(cleaned)

        # Ensure all speakers are mapped
        speaker_mapping = result.get("speakers", {})

        for item in transcript_data:
            if item["speaker"] not in speaker_mapping:
                speaker_mapping[item["speaker"]] = "Participant"

        return speaker_mapping

    except Exception as e:
        print("Role detection error:", str(e))

        # Better fallback
        unique_speakers = []
        for item in transcript_data:
            if item["speaker"] not in unique_speakers:
                unique_speakers.append(item["speaker"])

        fallback = {}

        for i, spk in enumerate(unique_speakers):
            if i == 0:
                fallback[spk] = "Moderator"
            else:
                fallback[spk] = f"Candidate {i}"

        return fallback

def generate_summary(transcript_data):
    full_text = " ".join(
        item["text"].strip()
        for item in transcript_data
        if item.get("text")
    )
    full_script = full_text

    return full_script

def classify_conversation(transcript):
    transcript_text = "\n".join(
        [f'{x["speaker"]}: {x["text"]}' for x in transcript]
    )

    prompt = f"""
    Analyze this transcript and return JSON only.

    Detect:
    - conversation_type
    - speaker roles

    Transcript:
    {transcript_text}
    """

    response = llm.invoke(prompt)

    return json.loads(response.content)

@celery_app.task
def process_meeting_audio(meeting_id, file_path):
    db = SessionLocal()

    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

        if not meeting:
            return {"error": "Meeting not found"}

        transcript_data = process_audio(file_path)

        # Auto role detection
        role_mapping = detect_speaker_roles(transcript_data)

        # Replace speaker ids with detected roles
        for item in transcript_data:
            item["speaker"] = role_mapping.get(
                item["speaker"],
                item["speaker"]
            )

        # Full transcript (store complete text)
        full_text = " ".join(
            item["text"].strip()
            for item in transcript_data
            if item.get("text")
        )

        # Save into DB
        meeting.transcribe = full_text   # Full script  
        meeting.transcript = transcript_data

        db.commit()
        db.refresh(meeting)

        print("Transcript and Summary saved successfully")

        return {
            "transcribe": full_text,
            "transcript": transcript_data
        }

    except Exception as e:
        print("Error:", str(e))

    finally:
        db.close()

