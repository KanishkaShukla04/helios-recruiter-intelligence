from fastapi import APIRouter
from pydantic import BaseModel

from app.parser.jd_parser import parse_job_description
from app.data.load_candidates import load_candidates
from app.ranker import candidate_fit_score

router = APIRouter()


# -----------------------------
# Request Model
# -----------------------------

class JobDescriptionRequest(BaseModel):
    job_description: str

# -----------------------------
# Parse JD
# -----------------------------

@router.post("/parse-jd")
def parse_jd(request: JobDescriptionRequest):
    print("========== /parse-jd HIT ==========")
    print(request.model_dump())

    role_dna = parse_job_description(request.job_description)

    return {
        "success": True,
        "role_dna": role_dna
    }


# -----------------------------
# Rank Candidates
# -----------------------------
@router.post("/rank")
def rank_candidates(request: JobDescriptionRequest):
    print("========== /rank HIT ==========")

    role_dna = parse_job_description(request.job_description)

    candidates = load_candidates()

    ranked = []

    for candidate in candidates:

     result = candidate_fit_score(
        candidate,
        role_dna
     )
    ranked.append({
        "candidate_id": candidate["candidate_id"],
        "name": candidate["profile"]["anonymized_name"],
        "current_title": candidate["profile"]["current_title"],
        "company": candidate["profile"]["current_company"],
        "title_match": result["title_match"],

        "score": result["score"],

        "skill_match": result["skill_match"],
        "experience_match": result["experience_match"],
        "industry_match": result["industry_match"],
        "location_match": result["location_match"],

        "matched_skills": result["matched_skills"],
        "reasons": result["reasons"]
    })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    return {
        "total_candidates": len(ranked),
        "role_dna": role_dna,
        "top_candidates": ranked[:20]
    }


# -----------------------------
# Candidate Lookup
# -----------------------------

@router.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: str):

    candidates = load_candidates(limit=100)
    print("Loaded candidates:", len(candidates))

    for candidate in candidates:

        if candidate["candidate_id"] == candidate_id:
            return candidate

    return {
        "error": "Candidate not found"
    }