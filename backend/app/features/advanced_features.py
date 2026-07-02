def get_skill_names(candidate):
    return [
        skill["name"]
        for skill in candidate.get("skills", [])
    ]


def get_companies(candidate):
    return [
        job["company"]
        for job in candidate.get("career_history", [])
    ]


def get_titles(candidate):
    return [
        job["title"]
        for job in candidate.get("career_history", [])
    ]