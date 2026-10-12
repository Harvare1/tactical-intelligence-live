"""Orchestrates the four-agent pipeline end to end.

    Event Analyzer -> Narrative Generator -> Grounding Checker -> Localization

Each stage only consumes the previous stage's typed output (list[Insight],
then per-insight text/GroundingResult/dict), which is what makes any one of
them swappable later (e.g. event_analyzer backed by a trained model,
narrative_generator backed by a real Foundry deployment) without touching
the others.
"""
import dataclasses

from core.models import Event, Insight

from agents.event_analyzer import EventAnalyzerAgent
from agents.grounding_checker import GroundingCheckerAgent
from agents.llm_backend import get_backend
from agents.localization_agent import LocalizationAgent
from agents.narrative_generator import NarrativeGeneratorAgent


class TacticalIntelligencePipeline:
    def __init__(self):
        self.event_analyzer = EventAnalyzerAgent()
        self.narrative_generator = NarrativeGeneratorAgent(get_backend())
        self.grounding_checker = GroundingCheckerAgent()
        self.localization_agent = LocalizationAgent()

    def run(self, events: list[Event]) -> list[Insight]:
        insights = self.event_analyzer.run(events)
        enriched = []
        for insight in insights:
            draft_text = self.narrative_generator.run(insight)
            grounding = self.grounding_checker.run(insight, draft_text)

            narrative = {"analyst_en": grounding.text, "grounded": str(grounding.grounded)}
            narrative.update({f"fan_{lang}": text for lang, text in self.localization_agent.run(insight).items()})

            enriched.append(dataclasses.replace(insight, narrative=narrative))
        return enriched
