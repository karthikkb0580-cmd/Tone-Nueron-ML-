"""Meeting adapter: transcript files plus a replaceable live-caption source.

Captions are normalised into ``TranscriptTurn`` objects. ``LiveCaptionSource`` is a thread-safe
queue stub you can feed from any caption SDK without changing Tone Neuron.
"""

from __future__ import annotations

import json
import re
import threading
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from tone_neuron.adapters.base import AdapterInput, combine_thread
from tone_neuron.schemas import AnalyzeContext, MeetingMeta, ReceiverInfo, TranscriptTurn

_SPEAKER_RE = re.compile(r"^(?P<speaker>[^:\n]{1,40}):\s*(?P<text>.+)$")
_VTT_TAG_RE = re.compile(r"<v\s+([^>]+)>")
_VTT_TIME_RE = re.compile(r"-->")


def parse_transcript_text(text: str) -> list[TranscriptTurn]:
    """Parse ``Speaker: line`` transcripts or WebVTT cues."""
    turns: list[TranscriptTurn] = []
    expect_new_cue = False
    last_speaker = "Speaker"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.upper().startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if _VTT_TIME_RE.search(line):
            expect_new_cue = True
            continue
        if line.isdigit() and len(line) < 5:
            continue
        tag = _VTT_TAG_RE.search(line)
        if tag:
            speaker = tag.group(1).strip()
            content = _VTT_TAG_RE.sub("", line).strip()
            turns.append(TranscriptTurn(speaker=speaker, text=content))
            last_speaker = speaker
            expect_new_cue = False
            continue
        match = _SPEAKER_RE.match(line)
        if match and len(match.group("speaker").split()) <= 5:
            speaker = match.group("speaker").strip()
            turns.append(TranscriptTurn(speaker=speaker, text=match.group("text").strip()))
            last_speaker = speaker
            expect_new_cue = False
            continue
        if expect_new_cue:
            turns.append(TranscriptTurn(speaker=last_speaker, text=line))
            expect_new_cue = False
        elif turns:
            turns[-1].text = f"{turns[-1].text} {line}".strip()
        else:
            turns.append(TranscriptTurn(speaker=last_speaker, text=line))
    return turns


def parse_transcript_file(path: str | Path) -> list[TranscriptTurn]:
    path = Path(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload.get("turns", []) if isinstance(payload, dict) else payload
        turns: list[TranscriptTurn] = []
        for item in items:
            if isinstance(item, dict):
                turns.append(
                    TranscriptTurn(
                        speaker=str(item.get("speaker", "Speaker")),
                        text=str(item.get("text", "")),
                        timestamp=item.get("timestamp"),
                        is_owner=bool(item.get("is_owner", False)),
                    )
                )
            elif isinstance(item, str):
                turns.extend(parse_transcript_text(item))
        return turns
    return parse_transcript_text(path.read_text(encoding="utf-8"))


class LiveCaptionSource:
    """Thread-safe stub for a live caption feed (replace with your meeting SDK)."""

    def __init__(self, max_lines: int = 500):
        self._turns: deque[TranscriptTurn] = deque(maxlen=max_lines)
        self._lock = threading.Lock()

    def push(self, line: str) -> TranscriptTurn | None:
        parsed = parse_transcript_text(line)
        if not parsed:
            return None
        with self._lock:
            self._turns.extend(parsed)
        return parsed[-1]

    def snapshot(self) -> list[TranscriptTurn]:
        with self._lock:
            return list(self._turns)

    def drain(self) -> list[TranscriptTurn]:
        with self._lock:
            turns = list(self._turns)
            self._turns.clear()
        return turns

    def session(self, owner: str = "me", title: str | None = None) -> "MeetingSession":
        session = MeetingSession(owner=owner, title=title, captions_are_live=True)
        for turn in self.snapshot():
            session.add_turn(turn)
        return session


@dataclass(slots=True)
class MeetingSession:
    owner: str = "me"
    title: str | None = None
    captions_are_live: bool = False
    duration_minutes: float | None = None
    starts_on_time: bool | None = None
    turns: list[TranscriptTurn] = field(default_factory=list)

    def add(self, speaker: str, text: str, timestamp: str | None = None) -> TranscriptTurn:
        turn = TranscriptTurn(
            speaker=speaker,
            text=text,
            timestamp=timestamp,
            is_owner=speaker.strip().lower() == self.owner.strip().lower(),
        )
        self.turns.append(turn)
        return turn

    def add_turn(self, turn: TranscriptTurn) -> None:
        if not turn.is_owner:
            turn.is_owner = turn.speaker.strip().lower() == self.owner.strip().lower()
        self.turns.append(turn)

    @property
    def participants(self) -> list[str]:
        seen: list[str] = []
        for turn in self.turns:
            if not turn.is_owner and turn.speaker not in seen:
                seen.append(turn.speaker)
        return seen

    def owner_text(self, limit: int = 8) -> str:
        lines = [turn.text for turn in self.turns if turn.is_owner][-limit:]
        return combine_thread(lines, limit=3000)

    def last_turn(self) -> TranscriptTurn | None:
        return self.turns[-1] if self.turns else None

    def context(self, target_language: str | None = None) -> AnalyzeContext:
        return AnalyzeContext(
            surface="meeting",
            target_language=target_language,
            meeting=MeetingMeta(
                title=self.title,
                participants=self.participants,
                duration_minutes=self.duration_minutes,
                captions_are_live=self.captions_are_live,
                starts_on_time=self.starts_on_time,
            ),
        )

    def to_input(
        self,
        receiver_name: str | None = None,
        target_language: str | None = None,
    ) -> AdapterInput:
        participants = self.participants
        receiver = ReceiverInfo(name=receiver_name or (participants[0] if participants else None))
        return AdapterInput(text=self.owner_text(), context=self.context(target_language), receiver=receiver)
