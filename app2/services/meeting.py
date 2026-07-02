from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import uuid
import os
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def create_google_meet():
    creds = None

    # Load token if exists
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            TOKEN_PATH,
            SCOPES
        )

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            os.remove(TOKEN_PATH)
            creds = None

    # If no token or invalid, login again
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH,
            SCOPES
        )

        creds = flow.run_local_server(port=0)

        # Save new token
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)

    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=365 * 50)

    event = {
        "summary": "Permanent Meeting Room",
        "start": {
            "dateTime": start_time.isoformat() + "Z"
        },
        "end": {
            "dateTime": end_time.isoformat() + "Z"
        },
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4())
            }
        }
    }

    event_result = service.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1
    ).execute()

    return event_result.get("hangoutLink")