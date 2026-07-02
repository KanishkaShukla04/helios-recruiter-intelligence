def experience_score(candidate_years, role_dna):
    """
    Returns a score between 0 and 1 based on how well the
    candidate's experience matches the JD.
    """

    required = role_dna.get("experience_min_years")

    # JD didn't mention experience
    if required is None:
        return 1.0

    # Candidate exceeds requirement
    if candidate_years >= required:
        return 1.0

    # Slightly below
    if candidate_years >= required - 1:
        return 0.8

    # Far below
    if candidate_years >= required - 2:
        return 0.5

    return 0.2