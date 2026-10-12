"""Core data model for synthetic match events and generated insights.

Pitch coordinates follow the convention x in [0, 105] (length, metres),
y in [0, 68] (width, metres), with team "home" always attacking toward x=105.
"""
from dataclasses import dataclass, field
from typing import Literal

EventType = Literal[
    "pass", "carry", "pressure", "duel", "shot", "goal",
    "turnover", "interception", "recovery",
]

Zone = Literal[
    "def_left", "def_center", "def_right",
    "mid_left", "mid_center", "mid_right",
    "att_left", "att_center", "att_right",
]


def zone_for(x: float, y: float) -> Zone:
    col = "left" if y < 68 / 3 else "right" if y > 2 * 68 / 3 else "center"
    row = "def" if x < 105 / 3 else "att" if x > 2 * 105 / 3 else "mid"
    return f"{row}_{col}"  # type: ignore[return-value]


@dataclass(frozen=True)
class Player:
    id: str
    team: Literal["home", "away"]
    name: str
    position: str  # e.g. "LWB", "ST", "CM"


@dataclass(frozen=True)
class Event:
    id: str
    minute: int
    second: int
    type: EventType
    team: Literal["home", "away"]
    player_id: str
    x: float
    y: float
    target_x: float | None = None
    target_y: float | None = None
    outcome: Literal["success", "failed"] = "success"

    @property
    def timestamp(self) -> str:
        return f"{self.minute:02d}:{self.second:02d}"

    @property
    def zone(self) -> Zone:
        return zone_for(self.x, self.y)


@dataclass(frozen=True)
class Evidence:
    """A pointer from an insight back to the raw events that justify it."""
    event_ids: list[str]
    metric: str
    value: float
    description: str


@dataclass(frozen=True)
class Insight:
    id: str
    minute: int
    category: Literal["pressing_trigger", "flank_overload", "progressive_channel", "control_shift"]
    team: Literal["home", "away"]
    headline: str
    evidence: Evidence
    confidence: float
    # Structured parameters (side, channel, counts) used by narrative/localization
    # templates, kept separate from free text so translating to another
    # language never requires parsing English sentences back apart.
    params: dict = field(default_factory=dict)
    narrative: dict[str, str] = field(default_factory=dict)  # lang -> text
