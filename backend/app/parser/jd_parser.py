"""
jd_parser.py — Helios Recruiter Intelligence
=============================================
Parses a raw Job Description string into a structured "Role DNA" dictionary.
Designed to be reusable across any software engineering role without
hard-coded domain values.

Usage::

    from app.parser.jd_parser import JDParser

    parser = JDParser()
    role_dna = parser.parse(jd_text)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Optional spaCy import — gracefully falls back to regex-only mode
# ---------------------------------------------------------------------------
try:
    import spacy

    _NLP = spacy.load("en_core_web_sm")
    _SPACY_AVAILABLE = True
except (ImportError, OSError):
    _NLP = None
    _SPACY_AVAILABLE = False
    logging.warning(
        "spaCy model 'en_core_web_sm' not found — falling back to regex extraction."
    )

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class RoleDNA:
    """Structured output of a parsed Job Description."""

    # Experience
    experience_min_years: Optional[float] = None
    experience_max_years: Optional[float] = None

    # Skills
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)

    # Technologies
    technologies: list[str] = field(default_factory=list)

    # Context
    industries: list[str] = field(default_factory=list)
    preferred_locations: list[str] = field(default_factory=list)

    # Culture / soft signals
    behavioral_preferences: list[str] = field(default_factory=list)

    # Negative signals — profiles that likely won't succeed
    negative_candidate_signals: list[str] = field(default_factory=list)

    # Raw metadata
    raw_text_length: int = 0

    def to_dict(self) -> dict:
        """Return a plain dict (JSON-serialisable)."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Taxonomy tables  — extend freely, never hard-coded per single JD
# ---------------------------------------------------------------------------

# Programming languages
_LANGUAGES: set[str] = {
    "python",
    "java",
    "scala",
    "kotlin",
    "go",
    "golang",
    "rust",
    "c++",
    "c#",
    "typescript",
    "javascript",
    "ruby",
    "swift",
    "r",
    "julia",
    "matlab",
    "php",
    "elixir",
    "haskell",
    "sql",
    "bash",
    "shell",
}

# ML / Data frameworks
_ML_FRAMEWORKS: set[str] = {
    "pytorch",
    "tensorflow",
    "keras",
    "jax",
    "huggingface",
    "transformers",
    "scikit-learn",
    "sklearn",
    "xgboost",
    "lightgbm",
    "catboost",
    "mlflow",
    "wandb",
    "ray",
    "dask",
    "spark",
    "pyspark",
    "langchain",
    "llamaindex",
    "llama-index",
    "openai",
    "anthropic",
    "vllm",
    "triton",
    "onnx",
    "tflite",
    "coreml",
}

# Infrastructure & DevOps
_INFRA: set[str] = {
    "aws",
    "gcp",
    "azure",
    "kubernetes",
    "k8s",
    "docker",
    "terraform",
    "helm",
    "airflow",
    "kafka",
    "rabbitmq",
    "redis",
    "elasticsearch",
    "opensearch",
    "postgresql",
    "mysql",
    "mongodb",
    "cassandra",
    "snowflake",
    "databricks",
    "bigquery",
    "redshift",
    "dbt",
    "fastapi",
    "flask",
    "django",
    "grpc",
    "graphql",
    "nginx",
    "github actions",
    "jenkins",
    "ci/cd",
    "prometheus",
    "grafana",
    "datadog",
}

# Vector / retrieval
_RETRIEVAL: set[str] = {
    "faiss",
    "pinecone",
    "weaviate",
    "milvus",
    "qdrant",
    "chroma",
    "pgvector",
    "ann",
    "hnsw",
    "rag",
    "retrieval-augmented generation",
    "vector search",
    "semantic search",
    "embedding",
    "embeddings",
}

ALL_TECH_TOKENS: set[str] = _LANGUAGES | _ML_FRAMEWORKS | _INFRA | _RETRIEVAL

# Behavioral / soft-skill patterns (regex fragments, case-insensitive)
_BEHAVIORAL_PATTERNS: list[tuple[str, str]] = [
    (r"cross[- ]functional", "cross-functional collaboration"),
    (r"ambiguous|ambiguity", "comfortable with ambiguity"),
    (r"ownership|accountab", "high ownership mindset"),
    (r"fast[- ]paced|high[- ]growth|startup", "thrives in fast-paced environments"),
    (r"self[- ]starter|self[- ]driven|proactive", "self-driven / proactive"),
    (r"communicate|communicat", "strong communication skills"),
    (r"mentor|coach|grow.{0,10}team", "mentorship / team growth focus"),
    (r"detail[- ]oriented|rigorous|attention to detail", "detail-oriented"),
    (r"collaborative|team player|team.{0,10}first", "collaborative team player"),
    (r"data[- ]driven|metrics[- ]driven|analytical", "data-driven decision making"),
    (r"bias.{0,10}action|ship|deliver", "bias toward action / shipping"),
    (r"mission[- ]driven|impact", "mission-driven mindset"),
]

# Negative signal patterns — profiles that recur in mismatch
_NEGATIVE_PATTERNS: list[tuple[str, str]] = [
    (
        r"only.{0,30}research|pure research|academic only",
        "pure-research profile (no production experience)",
    ),
    (
        r"consulting only|agency only|only.{0,20}consulting",
        "consulting-only background",
    ),
    (
        r"computer vision only|cv only|only.{0,20}computer vision",
        "computer-vision-only specialisation",
    ),
    (
        r"no.{0,20}production|never.{0,20}production|purely academic",
        "no production ML/engineering experience",
    ),
    (
        r"10\+.{0,20}year|15\+.{0,20}year|20\+.{0,20}year",
        "over-qualified senior (may expect mismatch in scope)",
    ),
    (
        r"prefer.{0,20}not.{0,20}manage|no.{0,20}manag",
        "strong preference against management path",
    ),
    (
        r"relocation not|not willing to relocat|remote only|fully remote only",
        "location inflexible (remote-only)",
    ),
]

# Industry taxonomy
_INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "fintech": [
        "fintech",
        "finance",
        "banking",
        "payments",
        "lending",
        "insurance",
        "trading",
        "wealth",
    ],
    "healthcare": [
        "healthcare",
        "health",
        "medical",
        "biotech",
        "pharma",
        "clinical",
        "genomics",
    ],
    "e-commerce": [
        "e-commerce",
        "ecommerce",
        "retail",
        "marketplace",
        "commerce",
        "supply chain",
    ],
    "enterprise saas": [
        "saas",
        "enterprise software",
        "b2b",
        "cloud software",
        "platform",
    ],
    "mobility": [
        "mobility",
        "logistics",
        "transportation",
        "fleet",
        "delivery",
        "last mile",
    ],
    "ai": [
        "ai platform",
        "ml platform",
        "foundation model",
        "llm",
        "generative ai",
        "genai",
    ],
    "social": [
        "social",
        "consumer",
        "media",
        "entertainment",
        "gaming",
        "creator",
    ],
    "security": [
        "security",
        "cybersecurity",
        "compliance",
        "infosec",
        "zero trust",
    ],
    "adtech": ["advertising", "adtech", "ad platform", "programmatic", "dsp"],
    "edtech": ["education", "edtech", "learning", "e-learning", "lms"],
}

# ---------------------------------------------------------------------------
# Experience extraction
# ---------------------------------------------------------------------------

# Ordered from most specific to least, to avoid greedy mismatch
_EXP_PATTERNS: list[re.Pattern] = [
    # "3–7 years", "3-7 yrs", "3 to 7 years"
    re.compile(
        r"(\d+(?:\.\d+)?)\s*[–\-–to]+\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
    # "3+ years", "minimum 3 years", "at least 3 years"
    re.compile(
        r"(?:minimum|at\s+least|min\.?|>\s*)?\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)"
        r"(?:\s+of)?\s+(?:relevant\s+)?(?:professional\s+)?(?:work\s+)?(?:experience|exp\.?)",
        re.IGNORECASE,
    ),
    # "experience: 5+ years"
    re.compile(
        r"experience\s*[:\-–]?\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
]


def _extract_experience(text: str) -> tuple[Optional[float], Optional[float]]:
    """
    Return (min_years, max_years) from free-form JD text.
    Returns (None, None) when no experience range is found.
    """
    for pattern in _EXP_PATTERNS:
        match = pattern.search(text)
        if match:
            groups = [g for g in match.groups() if g is not None]
            if len(groups) >= 2:
                lo, hi = float(groups[0]), float(groups[1])
                return (min(lo, hi), max(lo, hi))
            if len(groups) == 1:
                lo = float(groups[0])
                return (lo, None)
    return (None, None)


# ---------------------------------------------------------------------------
# Skills extraction helpers
# ---------------------------------------------------------------------------

# Markers that introduce a REQUIRED skills block
_REQUIRED_HEADERS = re.compile(
    r"(?:what you.{0,15}bring|requirements?|required|must[- ]have"
    r"|qualifications?|you have|you bring|you.{0,10}possess"
    r"|basic qualif|minimum qualif|you.{0,5}need)",
    re.IGNORECASE,
)

# Markers that introduce a PREFERRED skills block
_PREFERRED_HEADERS = re.compile(
    r"(?:nice[- ]to[- ]have|preferred|bonus|plus|preferred qualif"
    r"|additional|what would be great|desired|good to have|if you have)",
    re.IGNORECASE,
)

# Sentence / clause terminators
_CLAUSE_SPLIT = re.compile(r"[,;]|\band\b|\bor\b", re.IGNORECASE)

# Soft-skill noise words to strip when extracting skills
_SOFT_NOISE = re.compile(
    r"\b(ability|experience|background|knowledge|understanding|familiarity"
    r"|proficiency|working knowledge|expert|expertise|strong|solid|good|excellent"
    r"|great|deep|hands[- ]on|proven|demonstrated|track record|using|with"
    r"|in|of|the|a|an|to|and|or|for|is|are|have|has)\b",
    re.IGNORECASE,
)


def _clean_skill(raw: str) -> str:
    """Strip filler words and normalise whitespace from a raw skill fragment."""
    cleaned = _SOFT_NOISE.sub(" ", raw).strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" .,;:-()").lower()


def _extract_list_items(section_text: str) -> list[str]:
    """
    Extract bullet-point or sentence-style skill items from a text section.
    Returns cleaned, non-empty strings.
    """
    # Split on bullets / dashes / newlines
    lines = re.split(r"[\n•\-\*·]", section_text)
    items: list[str] = []
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        # Further split by comma/semicolon
        for fragment in _CLAUSE_SPLIT.split(line):
            fragment = fragment.strip()
            cleaned = _clean_skill(fragment)
            if cleaned and len(cleaned) > 2 and len(cleaned) < 120:
                items.append(cleaned)
    return items


def _section_text_after(header_pattern: re.Pattern, text: str) -> str:
    """
    Return the block of text immediately following a section header.
    Stops at the next section header (capitalised word + colon/newline).
    """
    match = header_pattern.search(text)
    if not match:
        return ""
    start = match.end()
    # Look for the next section break
    next_section = re.search(r"\n[A-Z][A-Za-z ]{2,30}[\:\n]", text[start:])
    end = start + next_section.start() if next_section else start + 1500
    return text[start:end]


# ---------------------------------------------------------------------------
# Technology extraction
# ---------------------------------------------------------------------------


def _extract_technologies(text: str) -> list[str]:
    """
    Return all technology tokens found in the text.
    Uses the curated ALL_TECH_TOKENS taxonomy.
    """
    text_lower = text.lower()
    found: list[str] = []
    for token in sorted(ALL_TECH_TOKENS):
        # Word-boundary match; handle tokens with special chars (c++, ci/cd)
        escaped = re.escape(token)
        if re.search(r"(?<!\w)" + escaped + r"(?!\w)", text_lower):
            found.append(token)
    return found


# ---------------------------------------------------------------------------
# Location extraction
# ---------------------------------------------------------------------------

_LOCATION_HEADER = re.compile(
    r"(?:location|office|based|hybrid|on[- ]?site|remote|work from)",
    re.IGNORECASE,
)

# Known city/country tokens for quick matching (extend as needed)
_LOCATION_TOKENS = re.compile(
    r"\b(bangalore|bengaluru|mumbai|delhi|hyderabad|pune|chennai|kolkata"
    r"|san francisco|new york|london|berlin|singapore|dubai|amsterdam"
    r"|remote|hybrid|on[- ]?site|india|usa|united states|uk|united kingdom"
    r"|canada|australia|germany|france)\b",
    re.IGNORECASE,
)


def _extract_locations(text: str) -> list[str]:
    """Return normalised location strings found in the JD."""
    matches = _LOCATION_TOKENS.findall(text)
    seen: set[str] = set()
    result: list[str] = []
    for m in matches:
        norm = m.strip().lower().replace("-", "").replace(" ", "-")
        if norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


# ---------------------------------------------------------------------------
# Industry detection
# ---------------------------------------------------------------------------


def _detect_industries(text: str) -> list[str]:
    """
    Match the JD text against industry taxonomy keyword lists.
    Returns canonical industry labels whose keywords appear in the text.
    """
    text_lower = text.lower()
    matched: list[str] = []
    seen: set[str] = set()
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords) and industry not in seen:
            matched.append(industry.lower())
            seen.add(industry.lower())
    return matched


# ---------------------------------------------------------------------------
# Behavioral signal extraction
# ---------------------------------------------------------------------------


def _extract_behavioral(text: str) -> list[str]:
    """
    Scan text for behavioral / culture preference signals.
    Returns a deduplicated list of human-readable labels.
    """
    found: list[str] = []
    seen: set[str] = set()
    for pattern, label in _BEHAVIORAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE) and label not in seen:
            found.append(label)
            seen.add(label)
    return found


# ---------------------------------------------------------------------------
# Negative signal extraction
# ---------------------------------------------------------------------------


def _extract_negative_signals(text: str) -> list[str]:
    """
    Detect linguistic markers that indicate profiles likely to *not* succeed
    in this role (consulting-only, pure-research, etc.).
    """
    found: list[str] = []
    seen: set[str] = set()
    for pattern, label in _NEGATIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE) and label not in seen:
            found.append(label)
            seen.add(label)
    return found


# ---------------------------------------------------------------------------
# spaCy-enhanced extraction
# ---------------------------------------------------------------------------


def _spacy_extract_skills(text: str) -> list[str]:
    """
    Use spaCy NER + noun chunk extraction to surface additional skill terms
    not captured by the regex taxonomy.  Falls back silently if spaCy is
    unavailable.
    """
    if not _SPACY_AVAILABLE or _NLP is None:
        return []

    doc = _NLP(text[:10_000])  # cap input to avoid latency spikes

    noun_chunks = [
        chunk.text.strip().lower()
        for chunk in doc.noun_chunks
        if 2 <= len(chunk.text.split()) <= 5  # multi-word technical phrases
    ]

    # Keep only chunks that look technical (contain a tech token or are short
    # proper nouns)
    tech_lower = {t.lower() for t in ALL_TECH_TOKENS}
    filtered = [
        chunk
        for chunk in noun_chunks
        if any(tok in chunk for tok in tech_lower)
        or (len(chunk.split()) == 1 and chunk[0].isupper())
    ]
    return list(dict.fromkeys(filtered))  # deduplicate, preserve order


# ---------------------------------------------------------------------------
# Main parser class
# ---------------------------------------------------------------------------


class JDParser:
    """
    Parses a raw Job Description string into a structured :class:`RoleDNA`.

    All extraction is stateless — the same instance can parse multiple JDs
    concurrently.

    Example::

        parser = JDParser()
        dna = parser.parse(jd_text)
        print(dna.to_dict())
    """

    def parse(self, jd_text: str) -> RoleDNA:
        """
        Parse *jd_text* and return a :class:`RoleDNA` instance.

        Parameters
        ----------
        jd_text:
            Raw text of the job description.  HTML should be stripped before
            passing.

        Returns
        -------
        RoleDNA
            Structured extraction result.
        """
        if not jd_text or not jd_text.strip():
            logger.warning("JDParser received empty text.")
            return RoleDNA()

        text = jd_text.strip()

        # --- Experience ---
        exp_min, exp_max = _extract_experience(text)

        # --- Section-aware skills ---
        required_section = _section_text_after(_REQUIRED_HEADERS, text)
        preferred_section = _section_text_after(_PREFERRED_HEADERS, text)

        required_skills = _extract_list_items(required_section) if required_section else []
        preferred_skills = (
            _extract_list_items(preferred_section) if preferred_section else []
        )

        # Augment with spaCy noun chunks if available
        if _SPACY_AVAILABLE:
            spacy_terms = _spacy_extract_skills(text)
            # Only add terms not already in required/preferred
            existing = set(required_skills + preferred_skills)
            for term in spacy_terms:
                if term not in existing:
                    required_skills.append(term)

        # Deduplicate while preserving order
        required_skills = list(dict.fromkeys(required_skills))
        preferred_skills = list(dict.fromkeys(preferred_skills))

        # --- Technologies ---
        technologies = _extract_technologies(text)

        # --- Industries ---
        industries = _detect_industries(text)

        # --- Locations ---
        preferred_locations = _extract_locations(text)

        # --- Behavioral preferences ---
        behavioral_preferences = _extract_behavioral(text)

        # --- Negative signals ---
        negative_signals = _extract_negative_signals(text)

        dna = RoleDNA(
            experience_min_years=exp_min,
            experience_max_years=exp_max,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            technologies=technologies,
            industries=industries,
            preferred_locations=preferred_locations,
            behavioral_preferences=behavioral_preferences,
            negative_candidate_signals=negative_signals,
            raw_text_length=len(text),
        )

        logger.info(
            "JDParser extracted: exp=(%s–%s), %d required skills, "
            "%d preferred skills, %d technologies, %d industries",
            exp_min,
            exp_max,
            len(required_skills),
            len(preferred_skills),
            len(technologies),
            len(industries),
        )
        return dna
    


# ---------------------------------------------------------------------------
# Unit-test examples (run with `python -m pytest jd_parser.py -v`)
# ---------------------------------------------------------------------------
def parse_job_description(jd_text: str) -> dict:
    """
    Convenience wrapper used by the FastAPI backend.
    """
    parser = JDParser()
    return parser.parse(jd_text).to_dict()

if __name__ == "__main__":
    import json

    _SAMPLE_JD = """
    Senior Machine Learning Engineer — Search & Retrieval

    About the Role
    We are looking for a Senior ML Engineer to join our Search Intelligence team
    at our Bangalore or San Francisco office (hybrid preferred). You will build
    and scale production retrieval systems that serve 50M+ daily queries.

    Requirements
    - 4–8 years of professional experience in machine learning or software engineering
    - Strong Python skills; experience with PyTorch or TensorFlow
    - Hands-on experience with vector databases: Faiss, Pinecone, or Weaviate
    - Production-level experience deploying models on AWS or GCP using Kubernetes
    - Solid understanding of SQL and distributed data systems (Spark, Kafka)
    - Experience building RAG or semantic search pipelines
    - Strong communication and ability to work cross-functionally with product and data teams

    Nice to Have
    - Experience with LangChain or LlamaIndex
    - Familiarity with MLflow or Weights & Biases
    - Contributions to open-source ML projects
    - Prior experience in fintech or e-commerce domains

    Culture
    We are a fast-paced, mission-driven startup. We value ownership, bias toward
    action, and teammates who are data-driven in every decision.  Self-starters
    who mentor junior engineers thrive here.

    Please note: Candidates with consulting-only or purely academic backgrounds
    will not be a fit. We are not looking for computer vision only specialists.
    """

    parser = JDParser()
    dna = parser.parse(_SAMPLE_JD)
    print(json.dumps(dna.to_dict(), indent=2))
