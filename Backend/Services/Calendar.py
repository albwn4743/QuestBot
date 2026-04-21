from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import datetime
import os.path
import pickle

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None

    # ✅ Load saved token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # ✅ If no valid creds → login once
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

        # ✅ Save token
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


def create_event(summary, description, start_time):
    service = get_calendar_service()

    now = datetime.datetime.now()

    # ✅ Strict validation instead of auto override
    if start_time < now:
        raise ValueError(f"Parsed time is in the past: {start_time}")

    end_time = start_time + datetime.timedelta(hours=1)

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
    }

    event_result = service.events().insert(
        calendarId='primary',
        body=event
    ).execute()

    return event_result.get('htmlLink')