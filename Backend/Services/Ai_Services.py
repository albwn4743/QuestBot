# from openai import OpenAI
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()
import json

client = Groq(api_key=os.getenv("GROK_API_KEY"))

def process_query(user_input, context=""):
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

    CRITICAL RULES:
    - If the user provides an email address (e.g., @gmail.com) OR asks you to send/write an email, "action" MUST BE EXACTLY "send_email".
    - ONLY use "general" if they are just asking a question and DO NOT want an email sent.
    
    JSON format:
    {{
    "action": "send_email", # or "general"
    "to": "the recipient's email address (if sending email)",
    "subject": "A professional subject line",
    "body": "The full professional email body containing the requested facts",
    "time": "ISO datetime if scheduling mentioned"
    }}

    If context is provided below, use it to ensure any factual information in the email is accurate.
    
    Context:
    {context}

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

def generate_answer(query, search_results, chat_history=None):
    if chat_history is None:
        chat_history = []
        
    context = ""
    for idx, res in enumerate(search_results):
        context += f"--- Document {idx + 1} ---\n"
        context += f"Source: {res.get('source', 'Unknown')}\n"
        context += f"Content: {res.get('text', '')}\n\n"

    system_prompt = f"""
    You are a professional assistant for Quest Innovative Solutions.
    Use the following retrieved context to answer the user's query.
    If the context does not contain the answer, simply state that you don't have enough information to answer that.
    
    IMPORTANT RULES:
    - Answer directly and naturally.
    - DO NOT start your response with filler phrases like "Based on the provided context...", "According to the documents...", or "Here are the details...".
    - Provide a clear, concise, and helpful answer.
    
    Context:
    {context}
    """

    messages = [{"role": "system", "content": system_prompt}]
    # Keep the last 6 messages for context
    messages.extend(chat_history[-6:])
    messages.append({"role": "user", "content": query})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    return response.choices[0].message.content