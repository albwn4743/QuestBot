import pdfplumber
from groq import Groq
# from openai import OpenAI
import json
import os
client = Groq(api_key="")


def extract_text(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text +=page.extract_text() + '\n'
    return text

# print(extract_text('D:\Data science notes\Projects\Quest\AlbinCV.pdf'))
def build_resume_prompt(text):
    return f"""
You are an expert resume analyzer.

Extract structured information from this resume.

Return ONLY JSON in this format:

{{
  "name": "",
  "skills": [],
  "projects": [
    {{
      "name": "",
      "tech": [],
      "description": ""
    }}
  ],
  "experience": [],
  "education": "",
  "strengths": []
}}

Resume:
{text}
"""

def analyze_resume(text):
    prompt = build_resume_prompt(text)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",   # or mixtral, llama3-70b
        messages=[
            {"role": "system", "content": "You are an expert interviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    res = response.choices[0].message.content
    return res
def build_question_prompt(structured,topic_type,topic_value,history):
    prompt=f'''
    You are a technical interviewer.

Ask ONE interview question based on:

Type: {topic_type}
Data: {topic_value}

Conversation so far:
{history}

Rules:
- Ask only one question
- Make it natural and conversational
- Avoid repeating previous questions
- Adjust difficulty slightly higher each time
'''

def evaluate_llm(structured,question,answer):
    prompt = f"""
You are an expert interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate:
1. Correctness (0-10)
2. Completeness
3. Missing points
4. Confidence level

Also generate:
- A follow-up question if needed

Return JSON:
{{
  "score": "",
  "feedback": "",
  "missing_points": "",
  "follow_up_question": ""
}}
"""
def parse_json(res):
    try:
        return json.loads(res)
    except:
        print('error')
        return {}
    
resume = extract_text('D:\Data science notes\Projects\Quest\AlbinCV.pdf')
structured = analyze_resume(resume)

print(structured)