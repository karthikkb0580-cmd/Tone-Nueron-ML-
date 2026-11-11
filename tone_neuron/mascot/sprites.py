"""Placeholder sprite resolution.

Sprites are emoji glyphs pulled from ``data/characters.json``. Drop a PNG/SVG with the same
filename into ``tone_neuron/mascot/sprites/`` and it is used instead — no code change needed.
"""

from __future__ import annotations

from pathlib import Path

from tone_neuron.cards import CardBook

SPRITE_DIR = Path(__file__).resolve().parent / "sprites"


def resolve_sprite(cards: CardBook, region: str | None, state: str) -> dict:
    character = cards.character(region)
    glyph, color = cards.sprite(region, state)
    sprite_rel = str(character.get("sprite", ""))
    candidate = SPRITE_DIR / Path(sprite_rel).name if sprite_rel else None
    return {
        "glyph": glyph,
        "color": color,
        "path": str(candidate) if candidate and candidate.exists() else None,
        "name": str(character.get("name", "Neuro")),
        "greeting": str(character.get("greeting", "")),
        "character": character,
    }
