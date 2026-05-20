from groq import Groq
from dotenv import load_dotenv
import os
import json
 
load_dotenv()
 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
 
def analyze_resume(resume_text, user_goal):
    prompt = f"""
You are a senior software engineer and hiring manager.
 
Evaluate the resume based on the user's goal.
 
User goal: "{user_goal}"
 
STRICT RULES:
- Extract only relevent skills for this goal
- REMOVE irrelevant tools [excel for backend, etc]
- Identify real gap
- Generate roadmap only for missing fields
- Make output DIFFERENT based on goal
 
return only JSON:
{{
"skills": [],
"missing_skills": [],
"roadmap": [],
"interview_questions": []
}}
Resume:
{resume_text}
"""
 
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You're a strict hiring manager. Return only valid JSON, no markdown, no backticks."},
                {"role": "user", "content": prompt}
            ]
        )
 
        content = response.choices[0].message.content.strip()
 
        # Markdown backticks clean kara
        content = content.replace("```json", "").replace("```", "").strip()
 
        start = content.find("{")
        end = content.rfind("}") + 1
 
        return json.loads(content[start:end])
 
    except Exception as e:
        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }
 