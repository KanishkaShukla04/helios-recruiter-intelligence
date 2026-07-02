from app.matcher import title_match
from app.scorer import experience_score


def candidate_fit_score(candidate, role_dna):
    profile = candidate["profile"]
    signals = candidate["redrob_signals"]

    score = 0

    skill_match = 0
    experience_match = 0
    industry_match = 0
    location_match = 0

    reasons = []

    # -------------------------
    # Experience
    # -------------------------

    years = profile.get("years_of_experience", 0)
    experience_match = experience_score(
    years,
    role_dna)
    score += experience_match * 30
    title_score = title_match(
    profile.get("current_title", ""),
    role_dna
)

    score += title_score * 20
    if title_score == 1:
     reasons.append("Relevant job title")

    elif title_score >= 0.7:
     reasons.append("Related engineering role")

    else:
     reasons.append("Different primary role")

    reasons.append(f"{years} years experience")

    # -------------------------
    # Technology Match
    # -------------------------

    candidate_skills = {
        s["name"].lower()
        for s in candidate.get("skills", [])
    }

    jd_tech = {
        t.lower()
        for t in role_dna.get("technologies", [])
    }
    matched_skills = []


    if jd_tech:
        matched = candidate_skills & jd_tech
        matched_skills = sorted(list(matched))
        return {
    "score": round(score, 2),
    "skill_match": round(skill_match * 100, 1),
    "experience_match": round(experience_match * 100, 1),
    "title_match": round(title_score * 100, 1),
    "industry_match": industry_match,
    "location_match": location_match,
    "matched_skills": matched_skills,
    "reasons": reasons
}
        skill_match = len(matched) / len(jd_tech)
        score += skill_match * 40

        if matched:
         reasons.append(
        "Matched skills: " + ", ".join(sorted(matched))
    )

    # -------------------------
    # Open to work
    # -------------------------

    if signals.get("open_to_work_flag"):
        score += 10
        reasons.append("Open to work")

    # -------------------------
    # Recruiter response
    # -------------------------

    response_rate = signals.get(
        "recruiter_response_rate",
        0
    )

    score += response_rate * 20

    # -------------------------
    # GitHub
    # -------------------------

    github = signals.get(
        "github_activity_score",
        0
    )

    score += github

    if github > 5:
        reasons.append("Active GitHub")

    # -------------------------

    return {
        "score": round(score, 2),
        "skill_match": round(skill_match * 100, 1),
        "experience_match": round(experience_match * 100, 1),
        "industry_match": industry_match,
        "location_match": location_match,
        "reasons": reasons
    }