def build_candidate_text(candidate):
    profile = candidate["profile"]

    skills = [
        skill["name"]
        for skill in candidate.get("skills", [])
    ]

    career_descriptions = [
        role.get("description", "")
        for role in candidate.get("career_history", [])
    ]

    text = f"""
    {profile.get('headline','')}
    {profile.get('summary','')}

    Skills:
    {' '.join(skills)}

    Experience:
    {' '.join(career_descriptions)}
    """

    return text
def extract_features(candidate):
    profile = candidate["profile"]
    signals = candidate["redrob_signals"]

    return {
        "candidate_id": candidate["candidate_id"],

        "years_experience":
            profile.get("years_of_experience", 0),

        "current_company":
            profile.get("current_company", ""),

        "current_title":
            profile.get("current_title", ""),

        "open_to_work":
            signals.get("open_to_work_flag", False),

        "response_rate":
            signals.get("recruiter_response_rate", 0),

        "saved_by_recruiters":
            signals.get("saved_by_recruiters_30d", 0),

        "github_score":
            signals.get("github_activity_score", -1),

        "notice_period":
            signals.get("notice_period_days", 999),
    }