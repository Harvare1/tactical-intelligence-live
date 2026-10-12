"""Rule-based tactical pattern detectors.

Every detector here only ever looks at `Event` objects and returns an
`Insight` whose `Evidence.event_ids` point back at the exact events that
justify it. Nothing downstream (narrative generation, localization) is
allowed to add claims that aren't traceable to this evidence — that
traceability is the whole "explainable AI" pitch of the project.
"""
from dataclasses import dataclass

from core.models import Event, Evidence, Insight

_EID = [0]


def _next_id() -> str:
    _EID[0] += 1
    return f"insight{_EID[0]}"


def _seconds(e: Event) -> int:
    return e.minute * 60 + e.second


def _cluster_by_time(items: list[tuple], key_time_idx: int, gap_seconds: int) -> list[list[tuple]]:
    """Group a time-sorted list into fixed-span windows.

    Comparing against the window's first item prevents a chain of individually
    close events from incorrectly becoming a match-long pattern.
    """
    if not items:
        return []
    clusters: list[list[tuple]] = [[items[0]]]
    for item in items[1:]:
        if item[key_time_idx] - clusters[-1][0][key_time_idx] <= gap_seconds:
            clusters[-1].append(item)
        else:
            clusters.append([item])
    return clusters


def detect_pressing_triggers(
    events: list[Event], regain_window_s: int = 6, regain_radius_m: float = 12.0,
    min_occurrences: int = 3, cluster_gap_s: int = 600,
) -> list[Insight]:
    by_team: dict[str, list[tuple]] = {"home": [], "away": []}
    turnovers = [e for e in events if e.type == "turnover"]
    recoveries_by_team = {
        "home": [e for e in events if e.type == "recovery" and e.team == "home"],
        "away": [e for e in events if e.type == "recovery" and e.team == "away"],
    }
    for to in turnovers:
        # a team presses and regains the ball IT just lost -> look at the *same* team's recovery
        pool = recoveries_by_team[to.team]
        for rec in pool:
            dt = _seconds(rec) - _seconds(to)
            if 0 <= dt <= regain_window_s:
                dist = ((rec.x - to.x) ** 2 + (rec.y - to.y) ** 2) ** 0.5
                if dist <= regain_radius_m:
                    by_team[to.team].append((_seconds(to), to, rec))
                    break

    insights = []
    for team, pairs in by_team.items():
        pairs.sort(key=lambda p: p[0])
        for cluster in _cluster_by_time(pairs, 0, cluster_gap_s):
            if len(cluster) < min_occurrences:
                continue
            event_ids = [eid for _, to, rec in cluster for eid in (to.id, rec.id)]
            start_minute = cluster[0][1].minute
            insights.append(Insight(
                id=_next_id(), minute=start_minute, category="pressing_trigger", team=team,
                headline=f"{team} wins the ball back within {regain_window_s}s of losing it, repeatedly",
                evidence=Evidence(
                    event_ids=event_ids, metric="regain_count", value=len(cluster),
                    description=(
                        f"{len(cluster)} regains within {regain_window_s}s and "
                        f"{regain_radius_m:.0f}m of the turnover, between "
                        f"{cluster[0][1].timestamp} and {cluster[-1][1].timestamp}."
                    ),
                ),
                confidence=min(0.95, 0.5 + 0.1 * len(cluster)),
                params={"regains": len(cluster), "window_s": regain_window_s},
            ))
    return insights


def detect_flank_overloads(
    events: list[Event], wide_band_m: float = 17.0, window_minutes: int = 3,
    min_share: float = 0.60, min_events: int = 8,
) -> list[Insight]:
    passes = [e for e in events if e.type == "pass"]
    insights = []
    for team in ("home", "away"):
        team_passes = sorted([e for e in passes if e.team == team], key=_seconds)
        if not team_passes:
            continue
        start_min = team_passes[0].minute - (team_passes[0].minute % window_minutes)
        end_min = team_passes[-1].minute + window_minutes
        for win_start in range(start_min, end_min, window_minutes):
            win_end = win_start + window_minutes
            window = [e for e in team_passes if win_start <= e.minute < win_end]
            if len(window) < min_events:
                continue
            left = [e for e in window if e.y <= wide_band_m]
            right = [e for e in window if e.y >= 68 - wide_band_m]
            for pitch_side, bucket in (("left", left), ("right", right)):
                share = len(bucket) / len(window)
                if share >= min_share and len(bucket) >= min_events:
                    # Convert fixed pitch coordinates into the attacking team's
                    # perspective. Away attacks in the opposite direction.
                    side = pitch_side if team == "home" else ("right" if pitch_side == "left" else "left")
                    insights.append(Insight(
                        id=_next_id(), minute=win_start, category="flank_overload", team=team,
                        headline=f"{team} is repeatedly overloading the {side} flank",
                        evidence=Evidence(
                            event_ids=[e.id for e in bucket], metric="flank_share", value=round(share, 2),
                            description=(
                                f"{len(bucket)} of {len(window)} buildup passes ({share:.0%}) between "
                                f"{win_start}' and {win_end}' came from within {wide_band_m:.0f}m of the "
                                f"{side} touchline."
                            ),
                        ),
                        confidence=min(0.95, share),
                        params={"side": side, "share": round(share, 2), "count": len(bucket)},
                    ))
                    break  # one flank-overload insight per window per team is enough
    return insights


def detect_progressive_channels(
    events: list[Event], min_progress_m: float = 20.0, cluster_gap_s: int = 600,
    min_occurrences: int = 4,
) -> list[Insight]:
    passes = [
        e for e in events
        if e.type == "pass" and e.target_x is not None
        and ((e.target_x - e.x) if e.team == "home" else (e.x - e.target_x)) >= min_progress_m
    ]
    insights = []
    for team in ("home", "away"):
        team_passes = sorted([e for e in passes if e.team == team], key=_seconds)
        tagged = [(_seconds(e), e) for e in team_passes]
        for cluster in _cluster_by_time(tagged, 0, cluster_gap_s):
            if len(cluster) < min_occurrences:
                continue
            evs = [e for _, e in cluster]
            avg_target_y = sum(e.target_y for e in evs if e.target_y is not None) / len(evs)
            channel = "right" if avg_target_y > 68 / 2 else "left"
            insights.append(Insight(
                id=_next_id(), minute=evs[0].minute, category="progressive_channel", team=team,
                headline=f"{team} is bypassing midfield through the {channel} channel",
                evidence=Evidence(
                    event_ids=[e.id for e in evs], metric="progressive_passes", value=len(evs),
                    description=(
                        f"{len(evs)} line-breaking passes of {min_progress_m:.0f}m+ into the {channel} "
                        f"channel between {evs[0].timestamp} and {evs[-1].timestamp}."
                    ),
                ),
                confidence=min(0.95, 0.4 + 0.1 * len(evs)),
                params={"channel": channel, "passes": len(evs)},
            ))
    return insights


def run_all_detectors(events: list[Event]) -> list[Insight]:
    insights = []
    insights += detect_pressing_triggers(events)
    insights += detect_flank_overloads(events)
    insights += detect_progressive_channels(events)
    insights.sort(key=lambda i: i.minute)
    return insights
