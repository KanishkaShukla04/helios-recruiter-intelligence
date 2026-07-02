def title_match(candidate_title, role_dna):
    """
    Returns:
        1.0 -> Excellent match
        0.7 -> Partial match
        0.2 -> Weak match
    """

    jd = " ".join(role_dna.get("required_skills", []))
    jd += " "
    jd += " ".join(role_dna.get("technologies", []))
    jd = jd.lower()

    title = candidate_title.lower()

    # Software Engineering
    if "software" in jd or "python" in jd or "backend" in jd:

        if any(word in title for word in [
            "software engineer",
            "backend",
            "full stack",
            "developer",
            "python"
        ]):
            return 1.0

        if any(word in title for word in [
            "devops",
            "data engineer",
            "ml engineer"
        ]):
            return 0.7

        return 0.2

    return 1.0