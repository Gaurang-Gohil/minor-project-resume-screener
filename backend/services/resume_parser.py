import google.generativeai as genai
import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

class ResumeParser:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        self.generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1
        )

    def parse_resume(self, resume_text: str) -> dict[str, Any]:
        """Parse a single resume text and return structured JSON"""
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
            response = self.model.generate_content(prompt, generation_config=self.generation_config)

            # Safely access content (Gemini sometimes returns candidate list)
            raw_text = response.candidates[0].content.parts[0].text.strip()
            # Parse JSON
            return json.loads(raw_text)

        except json.JSONDecodeError as je:
            print("JSON parsing failed:", je)
            return {"error": "Invalid JSON format from Gemini", "details": str(je)}

        except Exception as e:
            print("Gemini error:", e)
            return {"error": f"Gemini request failed: {str(e)}"}

    def parse_multiple_resumes(self, pdf_processor_output: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse multiple resume texts and return structured JSON responses"""
        parsed_results = []

        for pdf_data in pdf_processor_output:
            filename = pdf_data.get("filename", "unknown")

            try:
                if not pdf_data.get("extraction_success", False):
                    parsed_results.append({
                        "filename": filename,
                        "parsing_success": False,
                        "error": pdf_data.get("error", "Text extraction failed"),
                        "parsed_data": {}
                    })
                    continue

                resume_text = pdf_data.get("text_content", "").strip()

                if len(resume_text) < 50:
                    parsed_results.append({
                        "filename": filename,
                        "parsing_success": False,
                        "error": "Insufficient text content for parsing",
                        "parsed_data": {}
                    })
                    continue

                parsed_data = self.parse_resume(resume_text)

                if "error" in parsed_data:
                    parsed_results.append({
                        "filename": filename,
                        "parsing_success": False,
                        "error": parsed_data["error"],
                        "parsed_data": {}
                    })
                else:
                    parsed_results.append({
                        "filename": filename,
                        "parsing_success": True,
                        "parsed_data": parsed_data,
                        "text_length": pdf_data.get("text_length", len(resume_text))
                    })

            except Exception as e:
                parsed_results.append({
                    "filename": filename,
                    "parsing_success": False,
                    "error": str(e),
                    "parsed_data": {}
                })

        return parsed_results
