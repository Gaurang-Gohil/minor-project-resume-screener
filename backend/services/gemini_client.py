import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        genai.configure(api_key=api_key)

        # Correct model name, no prefix
        self.model = genai.GenerativeModel("gemini-2.5-pro")

    def test_connection(self):
        try:
            response = self.model.generate_content("Say hello!")
            return response.text
        except Exception as e:
            return f"Error connecting to Gemini API: {str(e)}"
