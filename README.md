# Helios Recruiter Intelligence
### Redrob Data & AI Challenge — AI-Powered Candidate Ranking Engine

---

## Architecture

```
helios/
├── backend/
│   ├── api/
│   │   └── main.py              # FastAPI — POST /rank, POST /parse-jd, GET /candidate/{id}
│   ├── app/
│   │   ├── parser/
│   │   │   └── jd_parser.py     # Role DNA extraction from raw JD text
│   │   ├── scoring/
│   │   │   ├── behavior_score.py  # Behavioral engagement scoring (12 signals)
│   │   │   └── semantic_score.py  # Sentence-transformer cosine similarity
│   │   └── llm/
│   │       └── reasoning.py     # Evidence-grounded recruiter explanations
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx         # Hero + JD input + results page
        │   └── layout.tsx
        └── components/
            ├── AIPipeline.tsx   # Animated 8-stage AI loading screen
            └── CandidateCard.tsx # Glassmorphism candidate card with reasoning
```

---

## Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run the API
uvicorn api.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`

---

## API Reference

### POST /parse-jd
Extract Role DNA from a job description.

```json
{
  "jd_text": "Senior ML Engineer — RAG, LLMs, Python..."
}
```

Returns:
```json
{
  "role_dna": {
    "experience_min_years": 4.0,
    "experience_max_years": 8.0,
    "required_skills": ["python", "pytorch", "vector databases"],
    "preferred_skills": ["langchain", "mlflow"],
    "technologies": ["python", "pytorch", "faiss", "kubernetes", "aws"],
    "industries": ["AI / ML platform"],
    "preferred_locations": ["Bangalore", "San Francisco"],
    "behavioral_preferences": ["bias toward action", "data-driven decision making"],
    "negative_candidate_signals": []
  }
}
```

---

### POST /rank
Rank candidates against a JD.

```json
{
  "jd_text": "...",
  "candidates": [...],
  "top_k": 20,
  "semantic_weight": 0.55,
  "behavior_weight": 0.45,
  "include_reasoning": true
}
```

---

### GET /candidate/{id}
Retrieve a previously ranked candidate.

---

## Scoring Model

| Signal | Weight |
|--------|--------|
| Semantic similarity (all-MiniLM-L6-v2) | 55% |
| Behavioral engagement | 45% |

**Behavioral sub-signals:**
- `open_to_work_flag` — active job search intent
- `recruiter_response_rate` — responsiveness to outreach
- `avg_response_time_hours` — speed of engagement
- `last_active_date` — recency of platform activity
- `saved_by_recruiters_30d` — organic demand signal
- `profile_views_received_30d` — visibility
- `interview_completion_rate` — reliability
- `offer_acceptance_rate` — genuine intent
- `github_activity_score` — technical signal
- `notice_period_days` — joinability
- `verified_email` / `verified_phone` — trust signals

---

## Environment Variables

```env
HELIOS_USE_LLM_REASONING=false   # Set true to enrich reasoning via Claude API
HELIOS_EMBED_BATCH_SIZE=256       # Embedding batch size (tune per RAM)
HELIOS_EMBED_CACHE_DIR=/tmp/helios_embed_cache
HELIOS_CORS_ORIGINS=http://localhost:3000
```