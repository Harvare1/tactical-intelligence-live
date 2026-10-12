"""Dependency-free HTTP entry point for imported and synthetic matches."""
import dataclasses
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from agents.pipeline import TacticalIntelligencePipeline
from core.match_generator import TEAM_NAMES, generate_match
from core.statsbomb_adapter import discover_matches
from engine import analyze, simulate

ROOT, STATIC = Path(__file__).parent, Path(__file__).parent / "static"


def build_sources():
    sources = {}
    for match_id, match in discover_matches().items():
        meta = match["meta"]
        sources[f"real:{match_id}"] = {
            "kind": "real", "meta": meta, "teams": {"home": meta["home"], "away": meta["away"]},
            "players": match["players"], "events": match["events"],
            "insights": TacticalIntelligencePipeline().run(match["events"]),
        }
    players, events = generate_match(seed=42)
    sources["synthetic"] = {
        "kind": "synthetic", "teams": TEAM_NAMES, "players": players, "events": events,
        "insights": TacticalIntelligencePipeline().run(events),
        "meta": {"id": "synthetic", "home": TEAM_NAMES["home"], "away": TEAM_NAMES["away"],
                 "competition": "Designed validation scenario", "date": "", "score": "1–0",
                 "duration": 90, "source": "Generated locally", "source_url": ""},
    }
    return sources


SOURCES = build_sources()
DEFAULT_SOURCE = next((key for key in SOURCES if key.startswith("real:")), "synthetic")
ROLLING_EVENTS = simulate(seed=42)


def _json(value):
    return json.dumps(value, separators=(",", ":")).encode()


def _source(query):
    key = query.get("source", [DEFAULT_SOURCE])[0]
    return key, SOURCES.get(key)


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        self.send_response(status); self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff"); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        route, query = urlparse(self.path), parse_qs(urlparse(self.path).query)
        if route.path == "/api/sources":
            rows = [{"key": key, "kind": item["kind"], **item["meta"]} for key, item in SOURCES.items()]
            return self._send(200, _json({"default": DEFAULT_SOURCE, "matches": rows}), "application/json")
        if route.path in ("/api/match", "/api/insights"):
            key, source = _source(query)
            if source is None:
                return self.send_error(404, "unknown source")
            if route.path == "/api/insights":
                return self._send(200, _json([dataclasses.asdict(i) for i in source["insights"]]), "application/json")
            body = {"source_key": key, "kind": source["kind"], "teams": source["teams"],
                    "meta": source["meta"], "players": [dataclasses.asdict(p) for p in source["players"]],
                    "events": [dataclasses.asdict(e) for e in source["events"]]}
            return self._send(200, _json(body), "application/json")
        if route.path == "/api/state":
            try:
                second = int(query.get("second", ["0"])[0])
                if not 0 <= second <= 5400: raise ValueError
            except (TypeError, ValueError):
                return self.send_error(400, "second must be between 0 and 5400")
            return self._send(200, _json(analyze(ROLLING_EVENTS, second)), "application/json")
        if route.path == "/health":
            return self._send(200, _json({"status": "ok", "matches": len(SOURCES)}), "application/json")
        relative = "index.html" if route.path == "/" else route.path.lstrip("/")
        target = (STATIC / relative).resolve()
        if STATIC.resolve() not in target.parents or not target.is_file(): return self.send_error(404)
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript": content_type += "; charset=utf-8"
        self._send(200, target.read_bytes(), content_type)

    def log_message(self, fmt, *args):
        if os.getenv("QUIET") != "1": super().log_message(fmt, *args)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080")); print(f"Tactical Intelligence Live · http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
