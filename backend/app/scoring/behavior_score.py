"""
behavior_score.py — Helios Recruiter Intelligence
==================================================
Computes a normalised behavioral engagement score (0–100) for a candidate
using Redrob platform signals.

Design goals
------------
* All weights are externally configurable via :class:`BehaviorWeights`.
* Every sub-score is clamped before weighting so a single extreme signal
  cannot dominate the composite.
* The module is stateless and dependency-free (stdlib only).

Usage::

    from app.scoring.behavior_score import BehaviorScorer, BehaviorWeights

    scorer = BehaviorScorer()
    result = scorer.score(candidate_signals)
    print(result.total_score)          # e.g. 74.3
    print(result.breakdown)            # per-signal contribution
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Weight configuration
# ---------------------------------------------------------------------------


@dataclass
class BehaviorWeights:
    """
    Relative importance weights for each behavioral signal.

    Weights are automatically normalised so they do not need to sum to 1.
    Increase a weight to make that signal more influential.

    Default calibration prioritises engagement signals (open_to_work,
    response rate) and professional quality indicators (offer acceptance,
    interview completion) over vanity metrics (profile views).
    """

    open_to_work_flag: float = 12.0
    """Binary flag: candidate has signalled active job search."""

    recruiter_response_rate: float = 15.0
    """
    0–1 fraction of recruiter messages the candidate replied to.
    High weight: unresponsive candidates waste sourcing effort.
    """

    avg_response_time_hours: float = 10.0
    """
    Average hours to respond. Lower is better.
    Scored inversely — fast responders score higher.
    """

    last_active_date: float = 8.0
    """Days since last platform activity. Lower is better."""

    saved_by_recruiters_30d: float = 6.0
    """Count of times saved by recruiters in last 30 days."""

    profile_views_received_30d: float = 4.0
    """Organic interest proxy — low weight (vanity metric)."""

    interview_completion_rate: float = 14.0
    """
    0–1 fraction of scheduled interviews the candidate completed.
    Crucial: ghosting interviews is a strong negative signal.
    """

    offer_acceptance_rate: float = 12.0
    """
    0–1 fraction of offers accepted when extended.
    High rate → genuine intent; low rate → offer shopping.
    """

    github_activity_score: float = 8.0
    """
    0–100 external score representing open-source / coding activity.
    Passed through with mild scaling.
    """

    notice_period_days: float = 6.0
    """
    Shorter notice periods score higher (faster joinability).
    Scored inversely.
    """

    verified_email: float = 3.0
    """Binary trust signal."""

    verified_phone: float = 2.0
    """Binary trust signal."""


# ---------------------------------------------------------------------------
# Candidate signal input schema
# ---------------------------------------------------------------------------


@dataclass
class CandidateSignals:
    """
    Raw behavioral platform signals for a single candidate.
    All fields are optional — missing values default to a neutral mid-score.
    """

    open_to_work_flag: bool = False
    recruiter_response_rate: Optional[float] = None  # 0.0–1.0
    avg_response_time_hours: Optional[float] = None  # hours
    last_active_date: Optional[datetime] = None
    saved_by_recruiters_30d: Optional[int] = None
    profile_views_received_30d: Optional[int] = None
    interview_completion_rate: Optional[float] = None  # 0.0–1.0
    offer_acceptance_rate: Optional[float] = None  # 0.0–1.0
    github_activity_score: Optional[float] = None  # 0–100
    notice_period_days: Optional[int] = None
    verified_email: bool = False
    verified_phone: bool = False


# ---------------------------------------------------------------------------
# Score result
# ---------------------------------------------------------------------------


@dataclass
class BehaviorScoreResult:
    """Output of :class:`BehaviorScorer`."""

    total_score: float
    """Normalised composite score in [0, 100]."""

    breakdown: dict[str, float]
    """Per-signal weighted contribution (sums to total_score)."""

    raw_sub_scores: dict[str, float]
    """Unweighted sub-score for each signal in [0, 100]."""

    metadata: dict = field(default_factory=dict)
    """Diagnostic metadata (missing signals, applied weights)."""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Sigmoid / clamping utilities
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _sigmoid_scale(x: float, midpoint: float, steepness: float = 0.1) -> float:
    """
    Map *x* to (0, 100) with a soft S-curve centred on *midpoint*.
    Useful for count-based signals with diminishing returns.
    """
    return 100.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


def _inverse_exp(value: float, half_life: float) -> float:
    """
    Score a 'lower is better' quantity using exponential decay.
    Returns 100 when value=0, decays toward 0 as value → ∞.
    half_life: the value at which score ≈ 50.
    """
    return 100.0 * math.exp(-math.log(2) * value / half_life)


# ---------------------------------------------------------------------------
# Sub-scorers
# ---------------------------------------------------------------------------

# Default neutral sub-score when a signal is absent
_NEUTRAL_SCORE = 50.0


def _score_open_to_work(flag: bool) -> float:
    return 100.0 if flag else 20.0


def _score_response_rate(rate: Optional[float]) -> float:
    if rate is None:
        return _NEUTRAL_SCORE
    return _clamp(rate * 100.0)


def _score_response_time(hours: Optional[float]) -> float:
    """Fast responders (< 4 hrs) → 100; slow (> 72 hrs) → near 0."""
    if hours is None:
        return _NEUTRAL_SCORE
    if hours <= 0:
        return 100.0
    return _clamp(_inverse_exp(hours, half_life=24.0))


def _score_last_active(last_active: Optional[datetime]) -> float:
    """Active today → 100; inactive 90+ days → 10."""
    if last_active is None:
        return _NEUTRAL_SCORE
    now = datetime.now(tz=timezone.utc)
    if last_active.tzinfo is None:
        last_active = last_active.replace(tzinfo=timezone.utc)
    days_ago = (now - last_active).total_seconds() / 86_400
    return _clamp(_inverse_exp(max(0, days_ago), half_life=14.0))


def _score_saved_by_recruiters(count: Optional[int]) -> float:
    """Sigmoid: 0 saves → 0, 5 saves → ~73, 10+ saves → ~90+."""
    if count is None:
        return _NEUTRAL_SCORE
    return _clamp(_sigmoid_scale(count, midpoint=4, steepness=0.5))


def _score_profile_views(count: Optional[int]) -> float:
    """Sigmoid centred at 50 views — diminishing returns after 100."""
    if count is None:
        return _NEUTRAL_SCORE
    return _clamp(_sigmoid_scale(count, midpoint=50, steepness=0.04))


def _score_interview_completion(rate: Optional[float]) -> float:
    """Strongly penalise ghosting: rate < 0.6 scores below 40."""
    if rate is None:
        return _NEUTRAL_SCORE
    # Apply a power curve to penalise low values more
    return _clamp((rate ** 1.5) * 100.0)


def _score_offer_acceptance(rate: Optional[float]) -> float:
    """
    Very low (<0.2) or very high (1.0) rates both signal risk.
    Optimal range is 0.5–0.85.
    """
    if rate is None:
        return _NEUTRAL_SCORE
    if rate < 0.0 or rate > 1.0:
        return _NEUTRAL_SCORE
    # Bell curve: peak at 0.7
    peak = 0.70
    width = 0.35
    return _clamp(100.0 * math.exp(-((rate - peak) ** 2) / (2 * width ** 2)))


def _score_github_activity(score: Optional[float]) -> float:
    """Pass-through; score already 0–100."""
    if score is None:
        return _NEUTRAL_SCORE
    return _clamp(float(score))


def _score_notice_period(days: Optional[int]) -> float:
    """0 days → 100 (immediate joiner); 90+ days → near 20."""
    if days is None:
        return _NEUTRAL_SCORE
    if days <= 0:
        return 100.0
    return _clamp(_inverse_exp(days, half_life=30.0))


def _score_verified_email(flag: bool) -> float:
    return 100.0 if flag else 30.0


def _score_verified_phone(flag: bool) -> float:
    return 100.0 if flag else 30.0


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------


class BehaviorScorer:
    """
    Computes a weighted behavioral engagement score for a candidate.

    Parameters
    ----------
    weights:
        An optional :class:`BehaviorWeights` instance. Pass a custom object
        to adjust signal importance for a specific role or company context.

    Example::

        # Use default weights
        scorer = BehaviorScorer()

        # Boost response-time importance for time-sensitive roles
        w = BehaviorWeights(avg_response_time_hours=20.0)
        fast_scorer = BehaviorScorer(weights=w)
    """

    def __init__(self, weights: Optional[BehaviorWeights] = None) -> None:
        self.weights = weights or BehaviorWeights()
        self._total_weight = sum(
            v for v in self.weights.__dict__.values() if isinstance(v, float)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, signals: CandidateSignals | dict) -> BehaviorScoreResult:
        """
        Compute the behavioral score for a candidate.

        Parameters
        ----------
        signals:
            Either a :class:`CandidateSignals` dataclass or a plain dict
            with the same field names (for easy integration with API layer).

        Returns
        -------
        BehaviorScoreResult
        """
        if isinstance(signals, dict):
            signals = self._dict_to_signals(signals)

        sub_scores = self._compute_sub_scores(signals)
        weighted, breakdown = self._apply_weights(sub_scores)

        result = BehaviorScoreResult(
            total_score=round(_clamp(weighted), 2),
            breakdown={k: round(v, 3) for k, v in breakdown.items()},
            raw_sub_scores={k: round(v, 2) for k, v in sub_scores.items()},
            metadata={
                "total_weight": self._total_weight,
                "signals_provided": self._count_provided(signals),
            },
        )

        logger.debug(
            "BehaviorScorer total=%.2f  breakdown=%s",
            result.total_score,
            result.breakdown,
        )
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _compute_sub_scores(self, s: CandidateSignals) -> dict[str, float]:
        return {
            "open_to_work_flag": _score_open_to_work(s.open_to_work_flag),
            "recruiter_response_rate": _score_response_rate(s.recruiter_response_rate),
            "avg_response_time_hours": _score_response_time(s.avg_response_time_hours),
            "last_active_date": _score_last_active(s.last_active_date),
            "saved_by_recruiters_30d": _score_saved_by_recruiters(
                s.saved_by_recruiters_30d
            ),
            "profile_views_received_30d": _score_profile_views(
                s.profile_views_received_30d
            ),
            "interview_completion_rate": _score_interview_completion(
                s.interview_completion_rate
            ),
            "offer_acceptance_rate": _score_offer_acceptance(s.offer_acceptance_rate),
            "github_activity_score": _score_github_activity(s.github_activity_score),
            "notice_period_days": _score_notice_period(s.notice_period_days),
            "verified_email": _score_verified_email(s.verified_email),
            "verified_phone": _score_verified_phone(s.verified_phone),
        }

    def _apply_weights(
        self, sub_scores: dict[str, float]
    ) -> tuple[float, dict[str, float]]:
        w = self.weights
        weight_map: dict[str, float] = {
            "open_to_work_flag": w.open_to_work_flag,
            "recruiter_response_rate": w.recruiter_response_rate,
            "avg_response_time_hours": w.avg_response_time_hours,
            "last_active_date": w.last_active_date,
            "saved_by_recruiters_30d": w.saved_by_recruiters_30d,
            "profile_views_received_30d": w.profile_views_received_30d,
            "interview_completion_rate": w.interview_completion_rate,
            "offer_acceptance_rate": w.offer_acceptance_rate,
            "github_activity_score": w.github_activity_score,
            "notice_period_days": w.notice_period_days,
            "verified_email": w.verified_email,
            "verified_phone": w.verified_phone,
        }
        total_weight = sum(weight_map.values())
        composite = 0.0
        breakdown: dict[str, float] = {}
        for signal, raw_score in sub_scores.items():
            w_val = weight_map.get(signal, 0.0)
            contribution = (w_val / total_weight) * raw_score
            composite += contribution
            breakdown[signal] = contribution
        return composite, breakdown

    @staticmethod
    def _dict_to_signals(d: dict) -> CandidateSignals:
        """Convert a plain dict to a :class:`CandidateSignals` instance."""
        last_active = d.get("last_active_date")
        if isinstance(last_active, str):
            try:
                last_active = datetime.fromisoformat(last_active)
            except ValueError:
                last_active = None

        return CandidateSignals(
            open_to_work_flag=bool(d.get("open_to_work_flag", False)),
            recruiter_response_rate=d.get("recruiter_response_rate"),
            avg_response_time_hours=d.get("avg_response_time_hours"),
            last_active_date=last_active,
            saved_by_recruiters_30d=d.get("saved_by_recruiters_30d"),
            profile_views_received_30d=d.get("profile_views_received_30d"),
            interview_completion_rate=d.get("interview_completion_rate"),
            offer_acceptance_rate=d.get("offer_acceptance_rate"),
            github_activity_score=d.get("github_activity_score"),
            notice_period_days=d.get("notice_period_days"),
            verified_email=bool(d.get("verified_email", False)),
            verified_phone=bool(d.get("verified_phone", False)),
        )

    @staticmethod
    def _count_provided(s: CandidateSignals) -> int:
        """Count how many optional signals were explicitly provided."""
        optional_fields = [
            s.recruiter_response_rate,
            s.avg_response_time_hours,
            s.last_active_date,
            s.saved_by_recruiters_30d,
            s.profile_views_received_30d,
            s.interview_completion_rate,
            s.offer_acceptance_rate,
            s.github_activity_score,
            s.notice_period_days,
        ]
        return sum(1 for f in optional_fields if f is not None)


# ---------------------------------------------------------------------------
# Unit-test examples
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from datetime import timedelta

    scorer = BehaviorScorer()

    # --- Highly engaged candidate ---
    strong = CandidateSignals(
        open_to_work_flag=True,
        recruiter_response_rate=0.95,
        avg_response_time_hours=3.0,
        last_active_date=datetime.now(tz=timezone.utc) - timedelta(hours=2),
        saved_by_recruiters_30d=8,
        profile_views_received_30d=120,
        interview_completion_rate=1.0,
        offer_acceptance_rate=0.75,
        github_activity_score=82.0,
        notice_period_days=15,
        verified_email=True,
        verified_phone=True,
    )
    r = scorer.score(strong)
    print(f"Strong candidate score: {r.total_score}")  # expect ~80–90

    # --- Passive / risky candidate ---
    passive = CandidateSignals(
        open_to_work_flag=False,
        recruiter_response_rate=0.20,
        avg_response_time_hours=96.0,
        last_active_date=datetime.now(tz=timezone.utc) - timedelta(days=45),
        saved_by_recruiters_30d=0,
        profile_views_received_30d=5,
        interview_completion_rate=0.40,
        offer_acceptance_rate=0.10,
        github_activity_score=5.0,
        notice_period_days=90,
        verified_email=False,
        verified_phone=False,
    )
    r2 = scorer.score(passive)
    print(f"Passive candidate score: {r2.total_score}")  # expect ~20–35

    # --- Dict input (API integration style) ---
    r3 = scorer.score(
        {
            "open_to_work_flag": True,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 6,
            "github_activity_score": 60,
            "notice_period_days": 30,
            "verified_email": True,
            "verified_phone": True,
        }
    )
    print(f"Dict input score: {r3.total_score}")
