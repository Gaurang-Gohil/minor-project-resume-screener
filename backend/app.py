from fastapi import FastAPI, Request, UploadFile, File
from dotenv import load_dotenv
from services.gemini_client import GeminiClient
from services.pdf_processor import PDFProcessor
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from services.resume_parser import ResumeParser
from fastapi import Form
import os
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Starting FastAPI app...")

# Create FastAPI app
app = FastAPI()

# Setup rate limiter with fallback IP method
def get_client_ip(request: Request):
    return request.client.host

limiter = Limiter(key_func=get_client_ip)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Root route
@app.get("/")
@limiter.limit("10/minute")
def root(request: Request):
    logger.info("Root endpoint hit.")
    return {"message": "Rate limit test successful"}

# Gemini test route
@app.get("/test-gemini")
def test_gemini():
    gemini = GeminiClient()
    result = gemini.test_connection()
    return {"response": result}

# PDF text extraction route
@app.post("/extract-pdf-text")
async def extract_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    with open("temp.pdf", "wb") as f:
        f.write(contents)

    pdf = PDFProcessor()
    text = pdf.extract_text("temp.pdf")
    return {"text": text}

@app.post("/parse-resume")
async def parse_resume(resume_text: str = Form(...)):
    parser = ResumeParser()
    result = parser.parse_resume(resume_text)
    return {"parsed": result}