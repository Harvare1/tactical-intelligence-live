from core.match_generator import generate_match


def test_generate_match_is_deterministic():
    players1, events1 = generate_match(seed=42)
    players2, events2 = generate_match(seed=42)
    assert [e.id for e in events1] == [e.id for e in events2]
    assert [(e.x, e.y) for e in events1] == [(e.x, e.y) for e in events2]


def test_generate_match_covers_full_90_minutes():
    _, events = generate_match(seed=42)
    assert events[0].minute == 0
    assert events[-1].minute <= 90
    assert max(e.minute for e in events) >= 85


def test_contains_a_goal():
    _, events = generate_match(seed=42)
    assert any(e.type == "goal" for e in events)


def test_22_players_generated():
    players, _ = generate_match(seed=42)
    assert len(players) == 22
    assert len({p.id for p in players}) == 22
