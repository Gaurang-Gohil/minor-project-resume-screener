import asyncio
from services.resume_scoring_service import RateLimitedResumeScorer

async def test_scoring():
    scorer = RateLimitedResumeScorer()
    job_description = "Looking for a Cloud Engineer with skills in AWS, Python, and Docker."

    parsed_resumes = [{
        "filename": "Gaurang.pdf",
        "parsed_data": {
            "name": "Gaurang",
            "email": "gaurang@example.com",
            "phone": "1234567890",
            "skills": ["Python", "AWS", "Docker"],
            "education": [{"degree": "B.Tech", "institution": "XYZ University", "year": "2024"}],
            "experience": [{"title": "Intern", "company": "Cloudify", "description": "Worked on CI/CD and automation"}]
        }
    }]

    results = await scorer.score_resume_batch(job_description, parsed_resumes)
    print("🎯 Scoring Results:\n", results)

if __name__ == "__main__":
    asyncio.run(test_scoring())
