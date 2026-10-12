"""Agent 4 — Localization Agent.

Produces a short, fan-facing one-liner per language, built from the
insight's structured `params` (not from parsing the English analyst
narrative) — so each language is phrased natively rather than machine
translated word-for-word, while still only ever stating exactly what the
detector found. Swap in Azure AI Translator here (set AZURE_TRANSLATOR_KEY)
for free-text translation of the full analyst narrative if that's ever
needed; the fan one-liners below stay template-based regardless, since they
are the thing least safe to leave to an uninspected translation call.
"""
from core.match_generator import TEAM_NAMES
from core.models import Insight

_FAN_TEMPLATES = {
    "en": {
        "pressing_trigger": "{team} keeps winning the ball straight back after losing it — the press is on.",
        "flank_overload": "{team} is building almost everything down the {side} side right now.",
        "progressive_channel": "{team} is skipping the midfield and going direct down the {channel} channel.",
        "control_shift": "{team} has taken the initiative — the rhythm of the match has shifted.",
    },
    "sv": {
        "pressing_trigger": "{team} vinner tillbaka bollen direkt efter varje bortfall — presset biter.",
        "flank_overload": "{team} bygger nästan allt via {side_sv} just nu.",
        "progressive_channel": "{team} hoppar över mittfältet och spelar direkt via {channel_sv}.",
        "control_shift": "{team} har tagit initiativet — matchrytmen har vänt.",
    },
    "es": {
        "pressing_trigger": "{team} recupera el balón casi al instante cada vez que lo pierde: la presión aprieta.",
        "flank_overload": "{team} está construyendo casi todo por el lado {side_es} ahora mismo.",
        "progressive_channel": "{team} se salta el mediocampo y juega directo por el carril {channel_es}.",
        "control_shift": "{team} ha tomado la iniciativa: el ritmo del partido ha cambiado.",
    },
}

_SIDE_SV = {"left": "vänsterkanten", "right": "högerkanten"}
_SIDE_ES = {"left": "izquierdo", "right": "derecho"}
_CHANNEL_SV = {"left": "vänsterkanalen", "right": "högerkanalen"}
_CHANNEL_ES = {"left": "izquierdo", "right": "derecho"}

SUPPORTED_LANGUAGES = ("en", "sv", "es")


class LocalizationAgent:
    name = "localization-agent"

    def run(self, insight: Insight, languages: tuple[str, ...] = SUPPORTED_LANGUAGES) -> dict[str, str]:
        team = TEAM_NAMES[insight.team]
        side = insight.params.get("side")
        channel = insight.params.get("channel")
        out = {}
        for lang in languages:
            template = _FAN_TEMPLATES[lang][insight.category]
            out[lang] = template.format(
                team=team,
                side=side, side_sv=_SIDE_SV.get(side, side), side_es=_SIDE_ES.get(side, side),
                channel=channel, channel_sv=_CHANNEL_SV.get(channel, channel),
                channel_es=_CHANNEL_ES.get(channel, channel),
            )
        return out
