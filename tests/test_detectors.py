from core.detectors import (
    detect_flank_overloads,
    detect_pressing_triggers,
    detect_progressive_channels,
    run_all_detectors,
)
from core.match_generator import generate_match


def test_pressing_trigger_detected_for_home():
    _, events = generate_match(seed=42)
    insights = detect_pressing_triggers(events)
    assert any(i.team == "home" for i in insights)
    found = next(i for i in insights if i.team == "home")
    assert 15 <= found.minute <= 40
    assert set(found.evidence.event_ids).issubset({e.id for e in events})


def test_flank_overload_detected_for_away():
    _, events = generate_match(seed=42)
    insights = detect_flank_overloads(events)
    assert any(i.team == "away" and i.params["side"] == "right" for i in insights)


def test_progressive_channel_detected_for_home():
    _, events = generate_match(seed=42)
    insights = detect_progressive_channels(events)
    assert any(i.team == "home" for i in insights)


def test_every_insight_evidence_is_grounded_in_real_events():
    _, events = generate_match(seed=42)
    event_ids = {e.id for e in events}
    insights = run_all_detectors(events)
    assert len(insights) >= 3
    for insight in insights:
        assert set(insight.evidence.event_ids).issubset(event_ids)
        assert len(insight.evidence.event_ids) > 0
