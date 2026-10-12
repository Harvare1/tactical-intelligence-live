"""Generic StatsBomb JSON adapter and local match discovery."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from core.models import Event, Player

DATA_DIR = Path(__file__).parents[1] / "data" / "statsbomb"


def _point(location, away=False):
    if not location or len(location) < 2:
        return None
    x, y = float(location[0]) / 120 * 105, float(location[1]) / 80 * 68
    return (105 - x, 68 - y) if away else (x, y)


def _teams(raw):
    ordered = []
    for item in raw:
        name = item.get("team", {}).get("name")
        if name and name not in ordered:
            ordered.append(name)
        if len(ordered) == 2:
            return ordered
    raise ValueError("StatsBomb file must contain events for two teams")


def load_match(path: Path, metadata: dict | None = None) -> tuple[list[Player], list[Event], dict]:
    """Normalize any StatsBomb events JSON file without match-specific code."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    home_name, away_name = _teams(raw)
    team_names = {home_name: "home", away_name: "away"}
    players: dict[str, Player] = {}
    events: list[Event] = []
    type_map = {"Pass": "pass", "Carry": "carry", "Pressure": "pressure",
                "Duel": "duel", "Interception": "interception", "Ball Recovery": "recovery"}

    for item in raw:
        # Period 5 is a penalty shootout, not open match play. The shootout
        # result belongs in metadata and must not distort tactical analysis.
        if item.get("period") == 5:
            continue
        team_name = item.get("team", {}).get("name")
        if team_name not in team_names:
            continue
        team = team_names[team_name]
        player_data = item.get("player") or {}
        player_id = str(player_data.get("id", f"unknown-{team}"))
        players.setdefault(player_id, Player(player_id, team, player_data.get("name", "Unknown player"), ""))
        kind_name = item.get("type", {}).get("name")
        payload = item.get(kind_name.lower().replace(" ", "_"), {}) if kind_name else {}
        kind = type_map.get(kind_name)
        if kind_name == "Shot":
            kind = "goal" if payload.get("outcome", {}).get("name") == "Goal" else "shot"
        if kind is None:
            continue
        start = _point(item.get("location"), team == "away")
        if start is None:
            continue
        end = _point(payload.get("end_location"), team == "away")
        outcome = payload.get("outcome", {}).get("name", "")
        failed = outcome in {"Incomplete", "Out", "Pass Offside", "Lost In Play", "Lost Out"}
        events.append(Event(id=f"sb-{item['id']}", minute=int(item.get("minute", 0)),
            second=int(item.get("second", 0)), type=kind, team=team, player_id=player_id,
            x=round(start[0], 2), y=round(start[1], 2),
            target_x=round(end[0], 2) if end else None, target_y=round(end[1], 2) if end else None,
            outcome="failed" if failed else "success",
            xg=float(payload.get("statsbomb_xg")) if payload.get("statsbomb_xg") is not None else None))

    events.sort(key=lambda event: (event.minute, event.second, event.id))
    score = Counter(event.team for event in events if event.type == "goal")
    supplied = metadata or {}
    meta = {
        "id": supplied.get("id", Path(path).stem), "home": home_name, "away": away_name,
        "score": supplied.get("score", f"{score['home']}–{score['away']}"),
        "date": supplied.get("date", ""), "competition": supplied.get("competition", "Imported match"),
        "source": supplied.get("source", "StatsBomb Open Data"),
        "source_url": supplied.get("source_url", "https://github.com/statsbomb/open-data"),
        "duration": max(event.minute for event in events), "raw_event_count": len(raw),
        "mapped_event_count": len(events),
    }
    return list(players.values()), events, meta


def discover_matches(directory: Path = DATA_DIR):
    catalog_path = directory / "catalog.json"
    catalog = json.loads(catalog_path.read_text()) if catalog_path.exists() else {}
    matches = {}
    for path in sorted(directory.glob("*.json")):
        if path.name == "catalog.json":
            continue
        players, events, meta = load_match(path, catalog.get(path.stem, {}))
        matches[str(meta["id"])] = {"players": players, "events": events, "meta": meta, "path": path}
    return matches
