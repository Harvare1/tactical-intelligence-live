"""Generates a synthetic, football-realistic match event stream.

The match is scripted around three deliberate tactical patterns so the
detectors in `detectors.py` have real, verifiable signal to find — this is
what keeps the later "explainable AI" claims honest: every insight traces
back to events actually present in this generated stream, not invented ones.

Pattern script (kept deterministic via `seed` so demos are repeatable):
  - 18'-34'  HOME presses AWAY high and wins the ball back within ~5s
             repeatedly after losing it in AWAY's defensive third.
  - 48'-63'  AWAY repeatedly overloads its right flank (home's left) during
             buildup, well above its share of play elsewhere on the pitch.
  - 69'-81'  HOME bypasses midfield with direct passes into the right
             channel behind the away left back.
"""
import random

from core.models import Event, Player

TEAM_NAMES = {"home": "Northside FC", "away": "Rivertown AFC"}

HOME_PLAYERS = [
    ("h_gk", "GK", "Odegaard-Smith"), ("h_rb", "RB", "Carter"), ("h_cb1", "CB", "Reyes"),
    ("h_cb2", "CB", "Mbeki"), ("h_lb", "LB", "Souza"), ("h_cm1", "CM", "Haaland Jr."),
    ("h_cm2", "CM", "Pirlo II"), ("h_rw", "RW", "Mensah"), ("h_am", "AM", "Larsson"),
    ("h_lw", "LW", "Dubois"), ("h_st", "ST", "Varga"),
]
AWAY_PLAYERS = [
    ("a_gk", "GK", "Fischer"), ("a_rb", "RB", "Oyelaran"), ("a_cb1", "CB", "Kowalski"),
    ("a_cb2", "CB", "Nilsen"), ("a_lb", "LB", "Petrov"), ("a_cm1", "CM", "Dahl"),
    ("a_cm2", "CM", "Herrera"), ("a_rw", "RW", "Sato"), ("a_am", "AM", "Costa"),
    ("a_lw", "LW", "Abiodun"), ("a_st", "ST", "Krajnc"),
]


def build_players() -> list[Player]:
    players = [Player(pid, "home", name, pos) for pid, pos, name in HOME_PLAYERS]
    players += [Player(pid, "away", name, pos) for pid, pos, name in AWAY_PLAYERS]
    return players


class _Clock:
    def __init__(self):
        self.minute = 0
        self.second = 0

    def advance(self, seconds: int):
        total = self.minute * 60 + self.second + seconds
        self.minute, self.second = divmod(total, 60)

    def tup(self):
        return self.minute, self.second


def _noise_phase(rng: random.Random, clock: _Clock, eid: list[int], team: str, duration: int) -> list[Event]:
    """A generic, unpatterned possession phase: a few passes drifting upfield."""
    events = []
    x, y = (10.0, 34.0) if team == "home" else (95.0, 34.0)
    direction = 1 if team == "home" else -1
    players = HOME_PLAYERS if team == "home" else AWAY_PLAYERS
    t = 0
    while t < duration:
        step = rng.randint(2, 5)
        clock.advance(step)
        t += step
        x = max(2.0, min(103.0, x + direction * rng.uniform(3, 10)))
        y = max(2.0, min(66.0, y + rng.uniform(-12, 12)))
        pid = rng.choice(players)[0]
        eid[0] += 1
        events.append(Event(
            id=f"e{eid[0]}", minute=clock.minute, second=clock.second,
            type="pass", team=team, player_id=pid, x=x, y=y,
            target_x=x + direction * rng.uniform(5, 15), target_y=y + rng.uniform(-8, 8),
            outcome="success" if rng.random() > 0.12 else "failed",
        ))
    return events


def _pressing_trigger_phase(rng: random.Random, clock: _Clock, eid: list[int]) -> list[Event]:
    """HOME loses the ball deep in AWAY's third, then wins it back in <5s. Repeat."""
    events = []
    for _ in range(5):
        clock.advance(rng.randint(8, 15))
        lose_x, lose_y = rng.uniform(75, 95), rng.uniform(10, 58)
        pid = rng.choice(HOME_PLAYERS)[0]
        eid[0] += 1
        events.append(Event(
            id=f"e{eid[0]}", minute=clock.minute, second=clock.second,
            type="turnover", team="home", player_id=pid, x=lose_x, y=lose_y,
        ))
        clock.advance(rng.randint(2, 5))  # the "within ~5s" window
        pid2 = rng.choice(HOME_PLAYERS)[0]
        eid[0] += 1
        events.append(Event(
            id=f"e{eid[0]}", minute=clock.minute, second=clock.second,
            type="recovery", team="home", player_id=pid2,
            x=lose_x + rng.uniform(-4, 4), y=lose_y + rng.uniform(-4, 4),
        ))
    return events


def _flank_overload_phase(rng: random.Random, clock: _Clock, eid: list[int]) -> list[Event]:
    """AWAY repeatedly builds down its right flank (y near 0, home's left side)."""
    events = []
    # A dense three-minute spell makes this pattern materially stronger than
    # natural touchline variation elsewhere in the synthetic match.
    for _ in range(40):
        clock.advance(rng.randint(3, 6))
        x = rng.uniform(40, 90)
        y = rng.uniform(0, 14)  # tight to the right touchline from away's attacking view
        pid = rng.choice([p for p in AWAY_PLAYERS if p[1] in ("RB", "RW", "AM", "CM")])[0]
        eid[0] += 1
        events.append(Event(
            id=f"e{eid[0]}", minute=clock.minute, second=clock.second,
            type="pass", team="away", player_id=pid, x=x, y=y,
            target_x=x - rng.uniform(5, 12), target_y=min(14, y + rng.uniform(0, 6)),
            outcome="success" if rng.random() > 0.1 else "failed",
        ))
    return events


def _progressive_channel_phase(rng: random.Random, clock: _Clock, eid: list[int]) -> list[Event]:
    """HOME bypasses midfield with direct line-breaking passes into the right channel."""
    events = []
    for _ in range(6):
        clock.advance(rng.randint(5, 9))
        x = rng.uniform(35, 55)
        y = rng.uniform(50, 64)  # home's right channel, behind the away left-back
        pid = rng.choice([p for p in HOME_PLAYERS if p[1] in ("CM", "RW", "AM")])[0]
        eid[0] += 1
        events.append(Event(
            id=f"e{eid[0]}", minute=clock.minute, second=clock.second,
            type="pass", team="home", player_id=pid, x=x, y=y,
            target_x=x + rng.uniform(25, 35), target_y=min(66, y + rng.uniform(0, 4)),
            outcome="success" if rng.random() > 0.15 else "failed",
        ))
    return events


def generate_match(seed: int = 42) -> tuple[list[Player], list[Event]]:
    rng = random.Random(seed)
    clock = _Clock()
    eid = [0]
    events: list[Event] = []

    def fast_forward_to(target_minute: int):
        while clock.minute < target_minute:
            team = rng.choice(["home", "away"])
            events.extend(_noise_phase(rng, clock, eid, team, duration=rng.randint(20, 40)))

    fast_forward_to(18)
    events.extend(_pressing_trigger_phase(rng, clock, eid))
    fast_forward_to(48)
    events.extend(_flank_overload_phase(rng, clock, eid))
    fast_forward_to(69)
    events.extend(_progressive_channel_phase(rng, clock, eid))
    fast_forward_to(90)

    eid[0] += 1
    events.append(Event(
        id=f"e{eid[0]}", minute=74, second=12, type="goal", team="home",
        player_id="h_rw", x=102.0, y=58.0,
    ))

    events.sort(key=lambda e: (e.minute, e.second, e.id))
    return build_players(), events
