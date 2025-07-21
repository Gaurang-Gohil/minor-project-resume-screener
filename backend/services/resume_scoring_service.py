import google.generativeai as genai
import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict

class RateLimitedResumeScorer:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")
        
        self.generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
        
        # Rate limiting: 4 resumes per minute
        self.resumes_per_minute = 4
        self.delay_between_requests = 15  # seconds

    async def score_resume_batch(self, job_description: str, parsed_resumes: List[Dict]) -> Dict:
        """Score resumes using structured JSON data from resume parser"""
        results = []
        successful_resumes = [r for r in parsed_resumes if r.get("parsing_success", False)]
        total_resumes = len(successful_resumes)
        
        for index, resume_data in enumerate(successful_resumes):
            try:
                score_result = await self.score_single_resume(
                    job_description, 
                    resume_data["parsed_data"],
                    resume_data["filename"]
                )
                
                results.append({
                    "filename": resume_data["filename"],
                    "candidate_name": resume_data["parsed_data"].get("name", "Unknown"),
                    "match_score": score_result.get("match_score", 0),
                    "detailed_scores": score_result,
                    "processed_at": datetime.now().isoformat()
                })
                
                # Rate limiting delay
                if index < total_resumes - 1:
                    await asyncio.sleep(self.delay_between_requests)
                    
            except Exception as e:
                results.append({
                    "filename": resume_data["filename"],
                    "error": str(e),
                    "match_score": 0
                })
        
        # Sort by score
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return {
            "total_processed": len(results),
            "processing_rate": f"{self.resumes_per_minute} resumes/minute",
            "results": results
        }

    async def score_single_resume(self, job_description: str, parsed_resume_json: dict, filename: str) -> dict:
        """Score resume using structured JSON data"""
        prompt = f"""
Compare this structured resume data against the job description:

JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME DATA:
{json.dumps(parsed_resume_json, indent=2)}

Return exact format:
{{
  "match_score": 85,
  "skill_match_score": 90,
  "experience_match_score": 80,
  "education_match_score": 85,
  "skillset_for_role": ["skill1", "skill2"],
  "overall_fit": "perfect/high/low/very low"
}}
"""

        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return json.loads(response.text)
        except Exception as e:
            return {"match_score": 0, "error": f"Scoring failed: {str(e)}"}
