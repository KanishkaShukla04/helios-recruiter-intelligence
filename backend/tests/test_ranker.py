from app.data.load_candidates import load_candidates
from app.ranker import candidate_fit_score

role_dna = {
    "technologies": [
        "python",
        "aws",
        "docker"
    ]
}

candidates = load_candidates(limit=5)

for c in candidates:
    result = candidate_fit_score(c, role_dna)

    print("-" * 50)
    print(c["profile"]["anonymized_name"])
    print(result)