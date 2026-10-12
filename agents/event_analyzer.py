"""Agent 1 — Event Analyzer.

Turns the raw synthetic event stream into structured tactical observations
(Insights with Evidence) using the rule-based detectors. Kept separate from
`core.detectors` deliberately: this is the seam where a future version could
swap in a learned/model-based detector without touching anything downstream
in the pipeline, as long as it still returns `Insight` objects with
evidence that traces back to real event ids.
"""
from core.detectors import run_all_detectors
from core.models import Event, Insight


class EventAnalyzerAgent:
    name = "event-analyzer"

    def run(self, events: list[Event]) -> list[Insight]:
        return run_all_detectors(events)
