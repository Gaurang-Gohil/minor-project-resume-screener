import google.generativeai as genai
import os
import json

class ResumeParser:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # This is the correct model name
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        
        # Configure for clean JSON output
        self.generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1
        )

    def parse_resume(self, resume_text: str) -> dict:
        prompt = f"""
Extract resume information and return as clean JSON:

Resume text: {resume_text}

Return format:
{{
  "name": "string",
  "email": "string", 
  "phone": "string",
  "skills": ["skill1", "skill2"],
  "education": [{{"degree": "string", "institution": "string", "year": "string"}}],
  "experience": [{{"title": "string", "company": "string", "description": "string"}}]
}}
"""

        try:
            response = self.model.generate_content(
                prompt, 
                generation_config=self.generation_config
            )
            return json.loads(response.text)
            
        except Exception as e:
            return {"error": str(e)}
