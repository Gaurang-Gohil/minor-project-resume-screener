import google.generativeai as genai
import os

class ResumeParser:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")

    def parse_resume(self, resume_text: str) -> dict:
        prompt = f"""
You are a resume parser.

Extract the following fields from the given resume text:
- Full Name
- Email
- Phone Number
- Skills
- Education
- Experience

Return the result strictly as a **valid JSON object**. Do NOT include any extra text, markdown, explanations, or formatting.

Resume:
\"\"\"
{resume_text}
\"\"\"
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return {"error": str(e)}
