"""Transparent in-match result forecast using only events visible at each checkpoint."""
from __future__ import annotations

import math

from core.models import Event


def _poisson(lam: float, goals: int) -> float:
    return math.exp(-lam) * lam ** goals / math.factorial(goals)


def forecast(events: list[Event], minute: int, regulation_minutes: int = 90) -> dict:
    if minute < 15:
        raise ValueError("first forecast is available at minute 15")
    visible = [event for event in events if event.minute <= minute and event.minute <= regulation_minutes]
    goals = {team: sum(event.team == team and event.type == "goal" for event in visible) for team in ("home", "away")}
    xg = {}
    shots = {}
    remaining = max(0, regulation_minutes - minute)
    for team in ("home", "away"):
        attempts = [event for event in visible if event.team == team and event.type in ("shot", "goal")]
        shots[team] = len(attempts)
        xg[team] = sum(event.xg if event.xg is not None else .10 for event in attempts)

    # League-neutral prior, increasingly replaced by this match's observed xG pace.
    prior_rate = 1.35
    evidence_weight = min(.78, minute / regulation_minutes * .78)
    lambdas = {}
    for team in ("home", "away"):
        observed_rate = min(4.5, xg[team] / max(minute, 1) * regulation_minutes)
        blended_rate = prior_rate * (1 - evidence_weight) + observed_rate * evidence_weight
        lambdas[team] = blended_rate * remaining / regulation_minutes

    outcomes = {"home": 0.0, "draw": 0.0, "away": 0.0}
    best = (0.0, goals["home"], goals["away"])
    for future_home in range(9):
        for future_away in range(9):
            probability = _poisson(lambdas["home"], future_home) * _poisson(lambdas["away"], future_away)
            final_home, final_away = goals["home"] + future_home, goals["away"] + future_away
            key = "home" if final_home > final_away else "away" if final_away > final_home else "draw"
            outcomes[key] += probability
            if probability > best[0]:
                best = (probability, final_home, final_away)
    total = sum(outcomes.values()) or 1
    probabilities = {key: round(value / total * 100, 1) for key, value in outcomes.items()}
    return {"minute": minute, "score": goals, "xg": {key: round(value, 2) for key, value in xg.items()},
            "shots": shots, "probabilities": probabilities,
            "most_likely_score": f"{best[1]}–{best[2]}", "model": "blended xG · Poisson v1",
            "experimental": True, "uses_future_events": False}


def forecast_timeline(events: list[Event]) -> list[dict]:
    return [forecast(events, minute) for minute in range(15, 86, 10)]
