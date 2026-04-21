from fastapi import FastAPI
from pydantic import BaseModel
from Services.Ai_Services import process_query
from Services.email_services import send_mail
from Services.Calendar import create_event
import json
import datetime

app = FastAPI()

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
def chat(request: ChatRequest):
    # raw_result = process_query(request.query)

    # Convert AI output → dict
    result = process_query(request.query)

    response_data = {}

    if result.get("action") == "send_email":

        # ✅ Handle multiple emails
        to_field = result.get("to")

        if isinstance(to_field, str):
            emails = [email.strip() for email in to_field.split(",")]
        else:
            emails = to_field

        # ✅ FIX: Convert body to string
        body = result.get("body")

        if isinstance(body, list):
            body = "\n".join(body)

        success_all = True

        for email in emails:
            success = send_mail(
                email,
                result.get("subject"),
                body
            )
            if not success:
                success_all = False

        response_data["email"] = "sent" if success_all else "partial_failed"
    # 📅 CREATE CALENDAR EVENT
    if result.get("time"):
        try:
            start_time = datetime.datetime.fromisoformat(result["time"])

            link = create_event(
                result.get("subject", "Event"),
                result.get("body", ""),
                start_time
            )

            response_data["calendar"] = "created"
            response_data["event_link"] = link

        except Exception as e:
            response_data["calendar"] = "failed"
            response_data["error"] = str(e)

    return response_data if response_data else result