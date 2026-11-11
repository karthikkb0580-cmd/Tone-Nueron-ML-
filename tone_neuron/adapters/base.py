"""Shared adapter primitives: every source produces an ``AdapterInput``."""

from __future__ import annotations

from dataclasses import dataclass, field

from tone_neuron.schemas import AnalyzeContext, MeetingMeta, ReceiverInfo


@dataclass(slots=True)
class AdapterInput:
    text: str
    context: AnalyzeContext = field(default_factory=AnalyzeContext)
    receiver: ReceiverInfo = field(default_factory=ReceiverInfo)

    def payload(self) -> dict:
        """JSON-ready body for ``POST /analyze`` or ``POST /gate``."""
        return {
            "text": self.text,
            "context": self.context.model_dump(),
            "receiver_info": self.receiver.model_dump(),
        }


def combine_thread(messages: list[str], limit: int = 6000) -> str:
    """Most-recent-last concatenation, truncated from the front."""
    joined = "\n\n---\n\n".join(message.strip() for message in messages if message and message.strip())
    if len(joined) <= limit:
        return joined
    return "…\n" + joined[-limit:]


def thread_receiver_hint(addresses: list[str]) -> str | None:
    """Pick the most likely recipient name from a thread's addresses."""
    for address in addresses:
        local = address.split("@")[0]
        cleaned = local.replace(".", " ").replace("_", " ").strip()
        if cleaned and not cleaned.isdigit():
            return cleaned.title()
    return None


def meeting_context(
    participants: list[str],
    title: str | None = None,
    duration_minutes: float | None = None,
    captions_are_live: bool = False,
) -> AnalyzeContext:
    return AnalyzeContext(
        surface="meeting",
        meeting=MeetingMeta(
            title=title,
            participants=participants,
            duration_minutes=duration_minutes,
            captions_are_live=captions_are_live,
        ),
    )
