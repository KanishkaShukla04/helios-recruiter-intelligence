from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Candidate:
    candidate_id: str
    profile: Dict[str, Any]
    career_history: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    redrob_signals: Dict[str, Any]