from fastapi import FastAPI
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import os
import boto3
import logging

session = boto3.session.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

s3 = session.client('s3')

# Import routers
from routers.resume_scoring_router import router as scoring_router

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Starting AI Resume Screening FastAPI app...")

# Create FastAPI app
app = FastAPI(
    title="AI Resume Screening Tool",
    description="AI-powered resume screening and scoring system using Gemini API",
    version="1.0.0"
)

# Setup rate limiter
def get_client_ip(request: Request):
    return request.client.host

limiter = Limiter(key_func=get_client_ip)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(scoring_router)

# Root route
@app.get("/")
@limiter.limit("10/minute")
def root(request: Request):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


