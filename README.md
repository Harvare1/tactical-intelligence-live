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
python -m unittest discover -s tests -v
docker build -t tactical-intelligence-live .
docker run --rm -p 8080:8080 tactical-intelligence-live
```

Useful endpoints:

- `GET /api/match` — scenario metadata
- `GET /api/insights` — the grounded multi-agent output
- `GET /api/state?second=3900` — rolling match state and evidence
- `GET /health` — container health probe

## How it works

The project contains two complementary demo paths. A typed four-stage pipeline detects scripted tactical patterns, creates evidence-citing narration, rejects unknown citations and localizes fan copy into English, Swedish and Spanish. A rolling-window engine generates linked possessions with passes, carries, recoveries and shots and evaluates four conservative rules:

1. right-channel pass concentration;
2. successful final-third entries;
3. pressure-linked recoveries;
4. shot volume and on-target count.

Each insight returns a stable key, audience-ready summary, analyst explanation, confidence label, supporting event IDs and an explicit limitation. This makes the computed evidence a safe grounding layer for a future Microsoft Foundry narrator.

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
- [ ] Azure Container Apps deployment
- [ ] Public GitHub repository and sub-two-minute demo video

No real club names, official match feeds, copyrighted footage, API keys or paid services are included.
