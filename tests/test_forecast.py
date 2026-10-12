from core.forecast import forecast, forecast_timeline
from core.statsbomb_adapter import DATA_DIR, load_match


def test_forecast_starts_at_15_and_updates_every_10_minutes():
    _, events, _ = load_match(DATA_DIR / "3943043.json")
    timeline = forecast_timeline(events)
    assert [item["minute"] for item in timeline] == [15, 25, 35, 45, 55, 65, 75, 85]


def test_forecast_probabilities_sum_to_100():
    _, events, _ = load_match(DATA_DIR / "3943043.json")
    for item in forecast_timeline(events):
        assert abs(sum(item["probabilities"].values()) - 100) < .2


def test_forecast_has_no_future_leakage():
    _, events, _ = load_match(DATA_DIR / "3943043.json")
    at_35 = forecast(events, 35)
    visible_only = forecast([event for event in events if event.minute <= 35], 35)
    assert at_35 == visible_only
    assert at_35["uses_future_events"] is False
