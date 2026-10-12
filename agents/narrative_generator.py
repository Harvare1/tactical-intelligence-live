"""Agent 2 — Narrative Generator.

Turns a grounded Insight into readable English commentary. Every sentence
this agent produces embeds the exact event ids it is based on (as
"[e12, e13]" citations) so Agent 3 (grounding_checker) can mechanically
verify nothing was invented. With a real LLM backend configured, the model
is only allowed to *phrase* the fixed evidence — it is given the evidence
numbers directly and instructed to cite them, not to infer new ones.
"""
from core.match_generator import TEAM_NAMES
from core.models import Insight

from agents.llm_backend import LLMBackend, TemplateBackend


def _cite(event_ids: list[str]) -> str:
    shown = event_ids[:4]
    suffix = f", +{len(event_ids) - 4} more" if len(event_ids) > 4 else ""
    return f"[{', '.join(shown)}{suffix}]"


_TEMPLATES = {
    "pressing_trigger": (
        "{team} is pressing with real intent here: {value:.0f} times now they've "
        "won the ball back within seconds of losing it. {desc} {cite}"
    ),
    "flank_overload": (
        "{team} keep going back to the same side — {value:.0%} of their buildup "
        "in this spell has come down one flank. {desc} {cite}"
    ),
    "progressive_channel": (
        "{team} are cutting out the midfield battle entirely. {value:.0f} "
        "line-breaking passes have gone straight into the same channel. {desc} {cite}"
    ),
}


class NarrativeGeneratorAgent:
    name = "narrative-generator"

    def __init__(self, backend: LLMBackend | None = None):
        # The template backend is the default on purpose: it guarantees the
        # citations below are byte-for-byte the real evidence ids, with zero
        # chance of model hallucination before grounding is even checked.
        self.backend = backend or TemplateBackend()

    def run(self, insight: Insight) -> str:
        template = _TEMPLATES[insight.category]
        text = template.format(
            team=TEAM_NAMES[insight.team],
            value=insight.evidence.value,
            desc=insight.evidence.description,
            cite=_cite(insight.evidence.event_ids),
        )
        if isinstance(self.backend, TemplateBackend):
            return text
        system = (
            "You are a football broadcast editor. Rewrite only the supplied observation "
            "in one concise sentence. Do not add tactics, causes, players, statistics or "
            "event ids. Preserve every bracketed evidence citation exactly."
        )
        try:
            generated = self.backend.generate(system, text).strip()
            return generated or text
        except Exception:
            # The live demo must remain deterministic if Foundry is unavailable.
            return text
