"""Deterministic synthetic football stream and explainable tactical rules."""
from __future__ import annotations

import random
from collections import Counter

TEAMS = ("Northbridge", "Riverside")


def _event(events, second, team, kind, x, y, end_x=None, end_y=None, **extra):
    item = {
        "id": f"e{len(events) + 1:04}", "second": int(second), "team": team,
        "type": kind, "x": round(max(0, min(100, x)), 1),
        "y": round(max(0, min(100, y)), 1),
        "end_x": round(max(0, min(100, x if end_x is None else end_x)), 1),
        "end_y": round(max(0, min(100, y if end_y is None else end_y)), 1),
        "success": extra.pop("success", True), "goal": extra.pop("goal", False),
    }
    item.update(extra)
    events.append(item)


def simulate(seed=42):
    """Build a coherent timeline with three deliberately testable stories."""
    rng = random.Random(seed)
    events, second, possession = [], 0, 0
    while second < 5400:
        minute = second / 60
        possession += 1
        team = rng.choices(TEAMS, [0.54, 0.46])[0]
        actions, x, y = rng.randint(2, 5), rng.uniform(12, 35), rng.uniform(12, 88)
        right_route = team == "Northbridge" and 55 <= minute <= 72 and rng.random() < .82
        if right_route:
            y = rng.uniform(72, 91)

        for sequence in range(actions):
            if second >= 5400:
                break
            pressure = team == "Riverside" and 24 <= minute <= 38 and x < 48 and rng.random() < .62
            if pressure:
                _event(events, second, team, "recovery", x, y, pressure=True,
                       possession=possession, sequence=sequence)
                second += rng.randint(7, 13)
            advance = rng.uniform(7, 19) + (7 if right_route else 0)
            target_y = rng.uniform(70, 94) if right_route else max(5, min(95, y + rng.uniform(-18, 18)))
            success = rng.random() < (0.89 if x < 68 else 0.76)
            kind = "carry" if rng.random() < .22 else "pass"
            _event(events, second, team, kind, x, y, x + advance, target_y,
                   success=success, pressure=pressure, possession=possession, sequence=sequence)
            if not success:
                break
            x, y = min(96, x + advance), target_y
            second += rng.randint(7, 16)
            shot_rate = .48 if 74 <= minute <= 84 and team == "Riverside" else .18
            if x >= 72 and rng.random() < shot_rate:
                on_target = rng.random() < .36
                goal = on_target and rng.random() < .24
                _event(events, second, team, "shot", x, y, 100, 50, success=on_target,
                       goal=goal, outcome="goal" if goal else ("saved" if on_target else "off target"),
                       possession=possession, sequence=sequence + 1)
                second += rng.randint(8, 18)
                break
        second += rng.randint(12, 30)
    return events


def _insight(key, team, title, short, explanation, limitation, evidence, confidence, metric, value):
    return {"key": key, "team": team, "title": title, "short": short,
            "explanation": explanation, "limitation": limitation,
            "evidence": [e["id"] for e in evidence], "confidence": confidence,
            "metric": metric, "value": value}


def analyze(events, second):
    """Analyze only evidence available at ``second`` in a rolling 10-minute window."""
    visible = [e for e in events if 0 <= e["second"] <= second]
    window = [e for e in visible if e["second"] > second - 600]
    insights = []
    for team in TEAMS:
        completed = [e for e in window if e["team"] == team and e["type"] in ("pass", "carry") and e["success"]]
        passes = [e for e in completed if e["type"] == "pass"]
        right = [e for e in passes if e["y"] >= 66.7]
        entries = [e for e in completed if e["x"] < 70 <= e["end_x"]]
        recoveries = [e for e in window if e["team"] == team and e["type"] == "recovery" and e.get("pressure")]
        shots = [e for e in window if e["team"] == team and e["type"] == "shot"]
        if len(passes) >= 8 and len(right) / len(passes) >= .62:
            share = len(right) / len(passes)
            insights.append(_insight("right_route", team, f"{team} are routing attacks down the right",
                f"{share:.0%} of completed passes began in the right channel.",
                f"{len(right)} of {len(passes)} completed passes began in the right third during the rolling ten-minute window.",
                "Event locations show ball usage, not an overload or a weakness in the opposition block.",
                right, "high" if len(right) >= 10 else "medium", "RIGHT-SIDE SHARE", f"{share:.0%}"))
        if len(entries) >= 4:
            insights.append(_insight("final_third", team, f"{team} are finding the final third",
                f"{len(entries)} successful entries in ten minutes.",
                f"{len(entries)} successful passes or carries crossed the 70% pitch line in the current window.",
                "Entries measure territory, not chance quality or defensive disruption.",
                entries, "high" if len(entries) >= 6 else "medium", "FINAL-THIRD ENTRIES", str(len(entries))))
        if len(recoveries) >= 3:
            insights.append(_insight("high_recovery", team, f"{team} are regaining the ball under pressure",
                f"{len(recoveries)} pressure-linked recoveries in ten minutes.",
                f"The event generator recorded {len(recoveries)} recoveries linked to pressure in the rolling window.",
                "This synthetic flag does not measure pressing shape, intensity or the opponent's available options.",
                recoveries, "medium", "PRESSURE RECOVERIES", str(len(recoveries))))
        if len(shots) >= 3:
            on_target = sum(e["success"] for e in shots)
            insights.append(_insight("shot_surge", team, f"{team} are building a shooting spell",
                f"{len(shots)} shots; {on_target} on target in ten minutes.",
                f"{team} produced {len(shots)} shots in the window, with {on_target} recorded on target.",
                "Volume is not quality. No xG, defender position or goalkeeper context is inferred.",
                shots, "high" if len(shots) >= 5 else "medium", "SHOT VOLUME", str(len(shots))))

    score = {team: sum(bool(e["goal"]) for e in visible if e["team"] == team) for team in TEAMS}
    counts = Counter(e["team"] for e in window if e["type"] in ("pass", "carry"))
    total = sum(counts.values()) or 1
    metrics = {team: {
        "share": round(counts[team] / total * 100),
        "shots": sum(e["team"] == team and e["type"] == "shot" for e in window),
        "entries": sum(e["team"] == team and e["type"] in ("pass", "carry") and e["success"] and e["x"] < 70 <= e["end_x"] for e in window),
    } for team in TEAMS}
    return {"second": second, "score": score, "insights": insights, "events": window,
            "metrics": metrics, "source": "Deterministic synthetic scenario · normalized attack-relative coordinates",
            "disclaimer": "Event evidence supports descriptive patterns only; it cannot establish formations, off-ball movement or causality."}
