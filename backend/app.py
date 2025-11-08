from dotenv import load_dotenv
load_dotenv()  # <-- must run before using os.getenv()

import os
import logging
import boto3
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Setup logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Starting AI Resume Screening FastAPI app...")

# CORS origins (adjust as needed)
origins = [
    "http://localhost",
    "http://localhost:3000",
]

# Create single FastAPI app instance
app = FastAPI(
    title="AI Resume Screening Tool",
    description="AI-powered resume screening and scoring system using Gemini API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter setup
def get_client_ip(request: Request):
    return request.client.host

limiter = Limiter(key_func=get_client_ip)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create boto3 session AFTER load_dotenv so envs exist
session = boto3.session.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
s3 = session.client('s3')

# Import and include routers after app exists
from routers.resume_scoring_router import router as scoring_router
app.include_router(scoring_router)

# Health endpoint (accept GET and HEAD)
@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return PlainTextResponse("ok")

# Root endpoint — allow GET and HEAD to avoid 405s on probes to /
@app.api_route("/", methods=["GET", "HEAD"])
@limiter.limit("10/minute")
async def root(request: Request):
    logger.info("Root endpoint hit.")
    return {
        "message": "AI Resume Screening Tool API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "batch_scoring": "/api/scoring/process-batch",
            "check_results": "/api/scoring/results/{task_id}",
            "test_endpoints": "/api/test/"
        }
    }

# Only used when you run python app.py locally; in CI use `python -m uvicorn app:app`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)