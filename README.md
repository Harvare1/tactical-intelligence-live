# Tactical Intelligence Live

**See the pattern. Check the evidence.**

Tactical Intelligence Live turns a deterministic, football-realistic event stream into concise live insights. Every claim links to the exact events that triggered it and includes a clear limitation. The demo is designed for Microsoft's *Inside the Game* developer hackathon.

## The demo

The 90-minute synthetic match contains three designed stories:

- **31′ — pressure:** Riverside records a cluster of pressure-linked recoveries.
- **65′ — right-side route:** Northbridge repeatedly progresses through the right channel.
- **80′ — shot surge:** Riverside builds a late spell of shots.

Switch between **Fan** and **Analyst** language, inspect the evidence IDs, filter the event stream, or play the match continuously. The interface never uses future events.

## Run locally

Python 3.10+ is the only runtime requirement.

```sh
python server.py
```

Open <http://localhost:8080>.

```sh
pytest -q
docker build -t tactical-intelligence-live .
docker run --rm -p 8080:8080 tactical-intelligence-live
```

Useful endpoints:

- `GET /api/sources` — which matches are loaded (synthetic, plus any real match dropped into `data/statsbomb/`)
- `GET /api/match?source=<key>` — players + event stream for a given source
- `GET /api/insights?source=<key>` — the grounded multi-agent output for that source
- `GET /api/state?second=3900` — the separate rolling-window engine's state and evidence
- `GET /health` — container health probe

## How it works

The project contains three complementary pieces:

1. **Agent pipeline** (`agents/`, `core/`) — a typed four-stage pipeline (Event Analyzer → Narrative Generator → Grounding Checker → Localization) that detects tactical patterns (pressing triggers, flank overloads, progressive channels), writes evidence-citing narration, mechanically rejects any citation outside the verified evidence, and localizes fan copy into English, Swedish and Spanish. This is what powers `/api/match` and `/api/insights`.
2. **Rolling-window engine** (`engine.py`) — a second, independent implementation generating linked possessions and evaluating four conservative rules (right-channel concentration, final-third entries, pressure-linked recoveries, shot volume) over a second-by-second window. Powers `/api/state`, kept as an alternate detection approach for comparison.
3. **Generic real-data adapter** (`core/statsbomb_adapter.py`) — discovers every StatsBomb event file in `data/statsbomb/`, infers teams, players, score and duration, normalizes coordinates and runs the same pipeline without match-specific code. **No real match data ships in the public repository**; `data/` is git-ignored and `/api/sources` falls back to the synthetic fixture when no local file exists.

The detectors cover pressing regains, flank concentration, progressive channels and five-minute **control shifts** derived from final-third entries, shots, pressure actions and recoveries. Each insight returns a stable id, narrative, supporting event IDs and confidence score.

## Import another real match

```sh
python -m scripts.import_statsbomb /path/to/events.json --id match-002 \
  --competition "Competition name" --date 2026-10-12
```

The source can also be an HTTPS raw-data URL. Restart `server.py`; the match appears in the selector automatically. Optional labels live in the ignored `data/statsbomb/catalog.json` file.

## Honest boundaries

The data is synthetic and both teams use attack-relative coordinates. It does not contain simultaneous player tracking. The product therefore does **not** infer formations, overloads, defensive weaknesses, off-ball movement, causality or xG. Confidence describes strength against a transparent rule threshold—not model certainty.

## Azure path

The container is ready for Azure Container Apps. Set `AZURE_FOUNDRY_ENDPOINT`, `AZURE_FOUNDRY_KEY` and optionally `AZURE_FOUNDRY_DEPLOYMENT` to enable server-side Foundry narration. Without credentials—or if the request fails—the system automatically uses deterministic grounded copy. Production deployment should replace the API key with managed identity.

## Submission checklist

- [x] Reproducible synthetic match and coherent possessions
- [x] Explainable, evidence-linked real-time observations
- [x] Polished responsive match centre
- [x] Fan and analyst modes
- [x] Docker image, health endpoint and CI tests
- [x] Optional Microsoft Foundry narration with deterministic fallback
- [x] Generic real-match adapter, validated locally against all 4,407 events from the 2022 World Cup final
- [x] Adaptive five-minute control-shift detection
- [ ] Azure Container Apps deployment
- [ ] Public GitHub repository and sub-two-minute demo video

The public repository ships only the fictional, synthetic match (`Northside FC`, `Rivertown AFC`, `Northbridge`, `Riverside`). No real club names, match feeds, copyrighted footage, API keys or paid services are committed to it. The StatsBomb adapter is parser code only — point it at your own locally downloaded open-data file to try it; the data itself is never part of this repo.
