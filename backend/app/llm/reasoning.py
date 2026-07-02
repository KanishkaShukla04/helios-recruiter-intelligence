"""
reasoning.py — Helios Recruiter Intelligence
============================================
Generates concise, evidence-grounded recruiter explanations for why a
candidate is (or isn't) a strong fit for a role.

Design principles
-----------------
* Zero hallucination: every sentence is anchored to evidence keys extracted
  from the candidate profile and score objects.
* Two operating modes:
  - **Template mode** (default): deterministic, fast, no external API calls.
  - **LLM mode**: enriches the template reasoning with a Claude API call for
    more natural phrasing.  Enable with ``use_llm=True``.
* The output is a single human-readable paragraph — suitable for display in
  a recruiter UI alongside scores.

Usage::

    from app.llm.reasoning import ReasoningEngine, ReasoningInput

    engine = ReasoningEngine()
    result = engine.generate(
        candidate=candidate_dict,
        jd_features=role_dna_dict,
        scores=scores_dict,
    )
    print(result.explanation)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Input / output types
# ---------------------------------------------------------------------------


@dataclass
class ScoreBundle:
    """Aggregated scores for a single candidate."""

    semantic_score: float  # 0–100
    behavior_score: float  # 0–100
    total_score: float  # 0–100


@dataclass
class ReasoningResult:
    """Output of :class:`ReasoningEngine`."""

    explanation: str
    """Recruiter-readable paragraph."""

    strengths: list[str]
    """Bullet-level strength signals extracted."""

    concerns: list[str]
    """Bullet-level concern signals extracted."""

    fit_label: str
    """One of: 'Strong Fit', 'Good Fit', 'Partial Fit', 'Weak Fit'."""

    confidence: float
    """0–1 confidence derived from score spread and evidence density."""


# ---------------------------------------------------------------------------
# Evidence extractors
# ---------------------------------------------------------------------------


def _years_experience(candidate: dict) -> Optional[float]:
    for key in ("years_experience", "total_experience_years", "experience_years"):
        if key in candidate:
            try:
                return float(candidate[key])
            except (ValueError, TypeError):
                pass
    return None


def _current_role(candidate: dict) -> Optional[str]:
    for key in ("current_title", "title", "current_role", "role"):
        if candidate.get(key):
            return str(candidate[key])
    return None


def _current_company(candidate: dict) -> Optional[str]:
    for key in ("current_company", "company", "employer"):
        if candidate.get(key):
            return str(candidate[key])
    return None


def _skills(candidate: dict) -> list[str]:
    for key in ("skills", "skill_set", "technical_skills", "tech_stack"):
        val = candidate.get(key)
        if isinstance(val, list):
            return [str(s) for s in val[:10]]
        if isinstance(val, str):
            return [s.strip() for s in val.split(",") if s.strip()]
    return []


def _notice_period(candidate: dict) -> Optional[int]:
    for key in ("notice_period_days", "notice_period", "notice"):
        val = candidate.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
    return None


def _github_score(candidate: dict) -> Optional[float]:
    val = candidate.get("github_activity_score") or candidate.get("github_score")
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def _open_to_work(candidate: dict) -> bool:
    return bool(candidate.get("open_to_work_flag", False))


def _location(candidate: dict) -> Optional[str]:
    for key in ("location", "city", "current_location"):
        if candidate.get(key):
            return str(candidate[key])
    return None


def _jd_technologies(jd_features: dict) -> list[str]:
    return jd_features.get("technologies", [])[:8]


def _jd_exp_min(jd_features: dict) -> Optional[float]:
    return jd_features.get("experience_min_years")


def _jd_preferred_locations(jd_features: dict) -> list[str]:
    return [loc.lower() for loc in jd_features.get("preferred_locations", [])]


# ---------------------------------------------------------------------------
# Fit label
# ---------------------------------------------------------------------------


def _fit_label(total: float) -> str:
    if total >= 78:
        return "Strong Fit"
    if total >= 62:
        return "Good Fit"
    if total >= 45:
        return "Partial Fit"
    return "Weak Fit"


def _confidence(semantic: float, behavior: float, n_strengths: int) -> float:
    """
    Confidence increases when both scores agree and evidence is rich.
    Returns a value in [0, 1].
    """
    agreement = 1.0 - abs(semantic - behavior) / 100.0
    evidence_density = min(n_strengths / 5.0, 1.0)
    return round((agreement * 0.6 + evidence_density * 0.4), 3)


# ---------------------------------------------------------------------------
# Template reasoning builder
# ---------------------------------------------------------------------------


class _TemplateReasoner:
    """
    Builds a recruiter-readable explanation using template rules.
    All statements are derived from passed-in evidence only.
    """

    def build(
        self,
        candidate: dict,
        jd_features: dict,
        scores: ScoreBundle,
    ) -> tuple[list[str], list[str], str]:
        """
        Return (strengths, concerns, explanation_paragraph).
        """
        strengths: list[str] = []
        concerns: list[str] = []

        # --- Experience ---
        years = _years_experience(candidate)
        jd_min = _jd_exp_min(jd_features)
        if years is not None:
            desc = f"{years:.1f} years of experience"
            if jd_min and years >= jd_min:
                strengths.append(desc + f" meets the {jd_min:.0f}+ year requirement")
            elif jd_min and years < jd_min:
                concerns.append(
                    f"{desc} is below the {jd_min:.0f}+ year requirement"
                )
            else:
                strengths.append(desc)

        # --- Role / company ---
        role = _current_role(candidate)
        company = _current_company(candidate)
        if role and company:
            strengths.append(f"currently {role} at {company}")
        elif role:
            strengths.append(f"currently works as {role}")

        # --- Skill / tech overlap ---
        cand_skills = set(s.lower() for s in _skills(candidate))
        jd_tech = set(t.lower() for t in _jd_technologies(jd_features))
        overlap = sorted(cand_skills & jd_tech)
        if overlap:
            top_overlap = ", ".join(overlap[:5])
            strengths.append(f"skill match on {top_overlap}")
        elif jd_tech and cand_skills:
            concerns.append("limited technology overlap with the JD requirements")

        # --- GitHub activity ---
        gh = _github_score(candidate)
        if gh is not None:
            if gh >= 70:
                strengths.append(f"strong GitHub activity score ({gh:.0f}/100)")
            elif gh <= 25:
                concerns.append(f"low GitHub activity ({gh:.0f}/100)")

        # --- Behavioral score ---
        if scores.behavior_score >= 75:
            strengths.append("high recruiter engagement and responsiveness")
        elif scores.behavior_score <= 35:
            concerns.append("low platform engagement / recruiter responsiveness")

        # --- Open to work ---
        if _open_to_work(candidate):
            strengths.append("actively seeking new opportunities")

        # --- Notice period ---
        notice = _notice_period(candidate)
        if notice is not None:
            if notice == 0:
                strengths.append("immediately available")
            elif notice <= 30:
                strengths.append(f"available within {notice} days")
            elif notice >= 60:
                concerns.append(f"{notice}-day notice period")

        # --- Location ---
        cand_loc = _location(candidate)
        preferred_locs = _jd_preferred_locations(jd_features)
        if cand_loc and preferred_locs:
            cand_loc_lower = cand_loc.lower()
            if any(p in cand_loc_lower or cand_loc_lower in p for p in preferred_locs):
                strengths.append(f"located in preferred region ({cand_loc})")

        # --- Semantic score context ---
        if scores.semantic_score >= 75:
            strengths.append(
                f"strong semantic alignment with JD ({scores.semantic_score:.0f}/100)"
            )
        elif scores.semantic_score <= 40:
            concerns.append(
                f"low semantic alignment with JD ({scores.semantic_score:.0f}/100)"
            )

        explanation = self._compose(candidate, scores, strengths, concerns)
        return strengths, concerns, explanation

    @staticmethod
    def _compose(
        candidate: dict,
        scores: ScoreBundle,
        strengths: list[str],
        concerns: list[str],
    ) -> str:
        name = candidate.get("name", "This candidate")
        label = _fit_label(scores.total_score)

        parts: list[str] = []

        if strengths:
            parts.append(
                f"{name} is a {label.lower()} — "
                + "; ".join(strengths[:4])
                + "."
            )
        else:
            parts.append(f"{name} scored {scores.total_score:.0f}/100 overall.")

        if concerns:
            concern_str = "; ".join(concerns[:3])
            parts.append(f"Main concern{'s' if len(concerns) > 1 else ''}: {concern_str}.")

        return " ".join(parts)


# ---------------------------------------------------------------------------
# LLM enrichment (optional)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a world-class technical recruiter assistant.
Your task is to rewrite a draft recruiter explanation into a single, polished,
evidence-driven paragraph (2–4 sentences).

RULES:
- Use ONLY the evidence provided. Never invent facts.
- Be specific: mention numbers (years, scores, days) when available.
- Be objective and professional.
- Do NOT use filler phrases like "I think" or "it seems".
- End with the main concern if one exists.
- Output ONLY the paragraph, no preamble, no bullet points."""


def _call_llm(draft: str, strengths: list[str], concerns: list[str]) -> str:
    """
    Optionally enrich a template draft using an LLM API call.
    Falls back to the draft if the call fails.
    """
    try:
        import httpx  # type: ignore

        evidence_block = "\n".join(
            [f"STRENGTH: {s}" for s in strengths]
            + [f"CONCERN: {c}" for c in concerns]
        )
        user_msg = (
            f"DRAFT:\n{draft}\n\n"
            f"EVIDENCE:\n{evidence_block}\n\n"
            "Rewrite the draft into a polished recruiter explanation using only the evidence above."
        )

        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 300,
                "system": _SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_msg}],
            },
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"].strip()
    except Exception as exc:
        logger.warning("LLM enrichment failed (%s) — using template draft.", exc)
        return draft


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------


class ReasoningEngine:
    """
    Generates recruiter explanations for candidate–JD matches.

    Parameters
    ----------
    use_llm:
        Whether to polish the explanation via LLM API call.
        Requires the ``ANTHROPIC_API_KEY`` env var or proxy to be configured.
        Defaults to ``False`` for zero-dependency / offline use.
    """

    def __init__(self, use_llm: bool = False) -> None:
        self.use_llm = use_llm
        self._template = _TemplateReasoner()

    def generate(
        self,
        candidate: dict[str, Any],
        jd_features: dict[str, Any],
        scores: dict[str, float] | ScoreBundle,
    ) -> ReasoningResult:
        """
        Generate a recruiter explanation.

        Parameters
        ----------
        candidate:
            Candidate profile dict (from your data layer).
        jd_features:
            RoleDNA dict from :class:`app.parser.jd_parser.JDParser`.
        scores:
            Either a :class:`ScoreBundle` or a plain dict with keys
            ``semantic_score``, ``behavior_score``, ``total_score``.

        Returns
        -------
        ReasoningResult
        """
        if isinstance(scores, dict):
            scores = ScoreBundle(
                semantic_score=float(scores.get("semantic_score", 50.0)),
                behavior_score=float(scores.get("behavior_score", 50.0)),
                total_score=float(scores.get("total_score", 50.0)),
            )

        strengths, concerns, draft = self._template.build(
            candidate, jd_features, scores
        )

        explanation = (
            _call_llm(draft, strengths, concerns) if self.use_llm else draft
        )

        return ReasoningResult(
            explanation=explanation,
            strengths=strengths,
            concerns=concerns,
            fit_label=_fit_label(scores.total_score),
            confidence=_confidence(
                scores.semantic_score, scores.behavior_score, len(strengths)
            ),
        )


# ---------------------------------------------------------------------------
# Unit-test examples
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    engine = ReasoningEngine(use_llm=False)

    candidate = {
        "name": "Priya Sharma",
        "current_title": "Senior ML Engineer",
        "current_company": "Flipkart AI Labs",
        "years_experience": 6.8,
        "skills": ["python", "pytorch", "faiss", "rag", "kubernetes", "aws"],
        "github_activity_score": 78,
        "open_to_work_flag": True,
        "notice_period_days": 60,
        "location": "Bangalore",
    }

    jd_features = {
        "experience_min_years": 4,
        "technologies": ["python", "pytorch", "faiss", "kubernetes", "aws", "mlflow"],
        "preferred_locations": ["bangalore", "san francisco", "remote"],
    }

    scores = ScoreBundle(semantic_score=81.3, behavior_score=77.5, total_score=79.4)

    result = engine.generate(candidate, jd_features, scores)
    print(f"[{result.fit_label}] (confidence={result.confidence})")
    print()
    print(result.explanation)
    print()
    print("Strengths:", result.strengths)
    print("Concerns :", result.concerns)
