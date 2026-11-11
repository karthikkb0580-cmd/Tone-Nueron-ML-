"""Collectible culture cards and the mascot character roster."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from tone_neuron.config import Settings, get_settings
from tone_neuron.schemas import CardsResponse, CultureCard


class CardBook:
    """Card tips live in ``data/cards.json``; unlock state is local and contains no content."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._lock = threading.Lock()
        self._cards_raw: list[dict] = []
        self._characters: list[dict] = []
        self._language_regions: dict[str, str] = {}
        self._state: dict[str, str] = {}
        self.reload()

    # -- loading -----------------------------------------------------------
    def reload(self) -> None:
        cards_doc = json.loads(Path(self.settings.cards_file).read_text(encoding="utf-8"))
        chars_doc = json.loads(Path(self.settings.characters_file).read_text(encoding="utf-8"))
        self._cards_raw = list(cards_doc.get("cards", []))
        self._characters = list(chars_doc.get("characters", []))
        self._language_regions = dict(chars_doc.get("language_regions", {}))
        state_file = Path(self.settings.state_dir) / "cards.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                if isinstance(state, dict):
                    self._state = {str(k): str(v) for k, v in state.get("unlocked", {}).items()}
            except (OSError, ValueError):
                self._state = {}

    def _persist(self) -> None:
        try:
            state_file = Path(self.settings.state_dir) / "cards.json"
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(
                json.dumps(
                    {"unlocked": self._state, "updated_at": datetime.now(timezone.utc).isoformat()},
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass  # unlock state is a nicety; never fail a request over it

    # -- cards -------------------------------------------------------------
    @property
    def regions(self) -> list[str]:
        return [str(card["region"]) for card in self._cards_raw]

    def _to_card(self, raw: dict) -> CultureCard:
        region = str(raw["region"])
        unlocked_at = self._state.get(region)
        return CultureCard(
            card_id=str(raw["id"]),
            region=region,
            region_name=str(raw["region_name"]),
            language=str(raw["language"]),
            character_name=self.character_name(region),
            sprite=self.character(region).get("sprite", ""),
            greeting_expression=self.character(region).get("greeting_expression", ""),
            greeting=str(raw["greeting"]),
            formality=str(raw["formality"]),
            dos=list(raw.get("dos", [])),
            donts=list(raw.get("donts", [])),
            taboo_topics=list(raw.get("taboo_topics", [])),
            caveat=str(raw.get("caveat", "")),
            unlocked=unlocked_at is not None,
            unlocked_at=unlocked_at,
        )

    def cards(self, region: str | None = None) -> CardsResponse:
        wanted = region.upper() if region else None
        cards = [
            self._to_card(raw)
            for raw in self._cards_raw
            if wanted is None or str(raw["region"]).upper() == wanted
        ]
        unlocked = sum(1 for card in cards if card.unlocked)
        active = wanted or self.settings.home_region
        return CardsResponse(
            cards=cards,
            unlocked_count=unlocked,
            total=len(cards),
            active_region=active,
        )

    def unlock(self, region: str, reason: str = "interaction") -> bool:
        region = (region or "").upper()
        if region not in self.regions:
            return False
        with self._lock:
            if region in self._state:
                return False
            self._state[region] = datetime.now(timezone.utc).isoformat()
            self._persist()
        return True

    def unlocked_regions(self) -> list[str]:
        return sorted(self._state)

    def card_for(self, region: str) -> CultureCard | None:
        for raw in self._cards_raw:
            if str(raw["region"]).upper() == region.upper():
                return self._to_card(raw)
        return None

    # -- characters --------------------------------------------------------
    def characters(self) -> list[dict]:
        return list(self._characters)

    def character(self, region: str | None) -> dict:
        region = (region or "").upper()
        for char in self._characters:
            if region in [str(r).upper() for r in char.get("regions", [])]:
                return char
        return self.default_character()

    def character_by_id(self, character_id: str) -> dict:
        for char in self._characters:
            if char.get("id") == character_id:
                return char
        return self.default_character()

    def default_character(self) -> dict:
        for char in self._characters:
            if char.get("kind") == "default":
                return char
        return self._characters[0] if self._characters else {"name": "Neuro", "states": {"idle": "🧠"}}

    def character_name(self, region: str | None) -> str:
        return str(self.character(region).get("name", "Neuro"))

    def region_for_language(self, language: str | None) -> str | None:
        if not language:
            return None
        language = language.strip()
        if language in self._language_regions:
            return self._language_regions[language].upper()
        base = language.split("-")[0].lower()
        for key, value in self._language_regions.items():
            if key.lower() == base:
                return value.upper()
        return None

    def sprite(self, region: str | None, state: str) -> tuple[str, str]:
        """Return (emoji glyph, colour) for a region character and state."""
        char = self.character(region)
        states = char.get("states", {})
        colors = char.get("colors", {})
        glyph = states.get(state) or states.get("idle") or "🧠"
        color = colors.get(state) or colors.get("idle") or "#7C9CFF"
        return str(glyph), str(color)

    def character_sprite(self, character_id: str, state: str) -> tuple[str, str]:
        char = self.character_by_id(character_id)
        states = char.get("states", {})
        colors = char.get("colors", {})
        return (
            str(states.get(state) or states.get("idle") or "🧠"),
            str(colors.get(state) or colors.get("idle") or "#7C9CFF"),
        )
