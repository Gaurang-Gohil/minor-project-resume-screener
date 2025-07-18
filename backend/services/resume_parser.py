import google.generativeai as genai
import os

class ResumeParser:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")

    def parse_resume(self, resume_text: str) -> dict:
        prompt = f"""
You are a resume parser. Extract the following fields from this resume:
- Full Name
- Email
- Phone Number
- Skills
- Education
- Experience

Give the output as JSON.

Resume:
{resume_text}
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return {"error": str(e)}
