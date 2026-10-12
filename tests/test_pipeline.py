from core.match_generator import generate_match

from agents.grounding_checker import GroundingCheckerAgent
from agents.pipeline import TacticalIntelligencePipeline


def test_pipeline_produces_grounded_narratives():
    _, events = generate_match(seed=42)
    insights = TacticalIntelligencePipeline().run(events)
    assert len(insights) >= 3
    for insight in insights:
        assert insight.narrative["grounded"] == "True"
        assert insight.narrative["analyst_en"]
        for lang in ("en", "sv", "es"):
            assert insight.narrative[f"fan_{lang}"]


def test_grounding_checker_rejects_fabricated_citations():
    _, events = generate_match(seed=42)
    insights = TacticalIntelligencePipeline().run(events)
    real_insight = insights[0]
    checker = GroundingCheckerAgent()

    fabricated_text = "This never happened [e99999]."
    result = checker.run(real_insight, fabricated_text)

    assert result.grounded is False
    assert "e99999" in result.unverifiable_ids
    assert result.text != fabricated_text


def test_grounding_checker_accepts_real_citations():
    _, events = generate_match(seed=42)
    insights = TacticalIntelligencePipeline().run(events)
    real_insight = insights[0]
    checker = GroundingCheckerAgent()

    real_id = real_insight.evidence.event_ids[0]
    result = checker.run(real_insight, f"Confirmed by event [{real_id}].")

    assert result.grounded is True
