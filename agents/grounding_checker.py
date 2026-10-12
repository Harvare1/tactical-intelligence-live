"""Agent 3 — Grounding Checker.

Mechanically verifies that every event id cited in a generated narrative
actually appears in that insight's evidence. This is the agent that keeps
the "explainable AI, not AI making things up" promise honest even if
Agent 2 is later swapped from the template backend to a real LLM: a model
that cites an event id outside the evidence set gets caught here, not
shipped to a viewer.
"""
import re
from dataclasses import dataclass

from core.models import Insight

_CITATION_RE = re.compile(r"\be\d+\b")

FALLBACK_TEXT = "Observation withheld: generated commentary referenced evidence outside the verified event set."


@dataclass(frozen=True)
class GroundingResult:
    text: str
    grounded: bool
    cited_ids: list[str]
    unverifiable_ids: list[str]


class GroundingCheckerAgent:
    name = "grounding-checker"

    def run(self, insight: Insight, narrative_text: str) -> GroundingResult:
        cited = sorted(set(_CITATION_RE.findall(narrative_text)))
        evidence_set = set(insight.evidence.event_ids)
        unverifiable = [c for c in cited if c not in evidence_set]
        if unverifiable:
            return GroundingResult(FALLBACK_TEXT, grounded=False, cited_ids=cited, unverifiable_ids=unverifiable)
        return GroundingResult(narrative_text, grounded=True, cited_ids=cited, unverifiable_ids=[])
