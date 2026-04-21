# from openai import OpenAI
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()
import json

client = Groq(api_key=os.getenv("GROK_API_KEY"))

def process_query(user_input):
    prompt = f"""
    You are a professional administrative assistant.

    Your job:
    1. Understand the user's request
    2. Extract action and email
    3. Generate a HIGHLY PROFESSIONAL email

    Email Rules:
- Write a clean, professional email
- DO NOT include any technical details like:
  - timestamps
  - ISO date formats
  - system data
  - calendar event details
- Write date in human format (e.g., April 20, 2026 at 1:00 PM)
- Keep tone formal and clear
- Keep it concise (not too long)
- No bullet points unless necessary
    - Closing must be:
    Best regards,
    Quest Innovative Solutions

    - If user mentions time → convert to ISO format
    - Include field "time": "YYYY-MM-DDTHH:MM:SS"
    - If no time → do not include
    - The email should sound like a real administrative message
    - Avoid unnecessary sections
    - Do not mention internal system actions like "scheduled in calendar"

    Output ONLY JSON

    JSON format:
    {{
    "action": "send_email or general",
    "to": "email if exists",
    "subject": "professional subject",
    "body": "full professional email",
    "time": "ISO datetime if scheduling mentioned"
    }}

    User Input: {user_input}
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": 'user', "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    content=response.choices[0].message.content
    try:
        return json.loads(content)
    except:
        return {"action": "general", "reply": content}