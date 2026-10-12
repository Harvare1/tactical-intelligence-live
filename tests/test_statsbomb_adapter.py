from core.statsbomb_adapter import DATA_DIR, discover_matches, load_match


def test_bundled_real_match_is_discovered_without_code_registration():
    matches = discover_matches()
    assert "3869685" in matches
    assert matches["3869685"]["meta"]["home"] == "Argentina"
    assert matches["3869685"]["meta"]["away"] == "France"


def test_statsbomb_events_are_normalized_and_traceable():
    players, events, meta = load_match(DATA_DIR / "3869685.json")
    assert len(players) >= 22
    assert len(events) > 2000
    assert meta["raw_event_count"] == 4407
    assert all(event.id.startswith("sb-") for event in events)
    assert all(0 <= event.x <= 105 and 0 <= event.y <= 68 for event in events)


def test_real_match_contains_detectable_goals():
    _, events, meta = load_match(DATA_DIR / "3869685.json")
    assert sum(event.type == "goal" for event in events) == 6
    assert meta["score"] == "3–3"
