from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from Services.Ai_Services import process_query, generate_answer
from Services.Dataset import connect_weaviate, get_embeddings, search_query
from Services.email_services import send_mail
from Services.Calendar import create_event
import json
import datetime

print("Initializing AI & Database connections...")
client = connect_weaviate()
embeddings = get_embeddings()
print("FastAPI Backend Ready!")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    client.close()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    query: str
    chat_history: List[Dict[str, Any]] = []

@app.post("/chat")
def chat(request: ChatRequest):
    # 1. ALWAYS retrieve database context first so the AI knows the facts
    search_results = search_query(request.query, client, embeddings)
    
    context_text = ""
    for idx, res in enumerate(search_results):
        context_text += f"Document {idx + 1}: {res.get('text', '')}\n"

    # 2. Extract intent and generate email USING the factual context
    result = process_query(request.query, context_text)

    response_data = {}

    is_admin_task = result.get("action") == "send_email" or result.get("time") is not None

    if is_admin_task:
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
            response_data["reply"] = "I have successfully sent the email." if success_all else "I tried to send the email, but encountered an issue."
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
            
            existing_reply = response_data.get("reply", "")
            response_data["reply"] = f"{existing_reply} I have also scheduled the calendar event.".strip()

        except Exception as e:
            response_data["calendar"] = "failed"
            response_data["error"] = str(e)

        return response_data if response_data else result
    
    else:
        # Fallback to RAG Search for general questions (reuse the search_results)
        answer = generate_answer(request.query, search_results, request.chat_history)
        
        return {
            "reply": answer,
            "action": "general"
        }