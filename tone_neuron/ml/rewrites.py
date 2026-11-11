"""Task C: region-appropriate rewrite suggestions, grounded in retrieved OKF entries.

The default rewriter is deterministic and offline. When an OpenAI-compatible endpoint is
configured, the LLM path is used and is given only the message plus the retrieved etiquette
snippets, with instructions not to invent cultural rules.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Iterable

from tone_neuron.config import Settings, get_settings
from tone_neuron.knowledge.okf import KnowledgeEntry
from tone_neuron.knowledge.store import KnowledgeIndex
from tone_neuron.schemas import FlaggedSpan, Rewrite

URGENCY_RE = re.compile(r"\b(asap|immediately|right away|right now|urgent)\b", re.IGNORECASE)
GREETING_RE = re.compile(
    r"^\s*(dear|hi\b|hello|hey\b|good morning|good afternoon|good evening|"
    r"お世話|いつも|您好|尊敬的|ol[áa]|oi\b|bom dia|as-salaam|assalam|guten tag|"
    r"sehr geehrte|hallo)",
    re.IGNORECASE,
)

CLOSINGS: dict[str, str] = {
    "JP": "よろしくお願いいたします。",
    "IN": "Warm regards,",
    "DE": "Mit freundlichen Grüßen",
    "US": "Thanks,",
    "UK": "Kind regards,",
    "CN": "谢谢！",
    "BR": "Abraço,",
    "AE": "Best regards,",
}

COURTESY: dict[str, str] = {
    "JP": "ご確認いただけますと幸いです。",
    "IN": "Kindly confirm at your earliest convenience.",
    "DE": "Vielen Dank im Voraus.",
    "US": "Thanks so much for your help with this.",
    "UK": "I would be grateful for your thoughts when you have a moment.",
    "CN": "麻烦您确认一下，谢谢。",
    "BR": "Muito obrigado pela ajuda!",
    "AE": "We would appreciate your guidance.",
}


def _first_and_last(name: str | None) -> tuple[str, str]:
    if not name:
        return "", ""
    parts = [part for part in name.split() if part]
    if not parts:
        return "", ""
    return parts[0], parts[-1]


def display_name(name: str | None, region: str) -> str:
    first, last = _first_and_last(name)
    if not first:
        return ""
    region = region.upper()
    if region == "JP":
        return f"{last}-san"
    if region == "CN":
        return f"{last}经理"
    if region in ("IN", "AE", "DE", "UK"):
        return f"{first} {last}" if last else first
    return first


def greeting_for(region: str, name: str | None) -> str:
    region = region.upper()
    display = display_name(name, region)
    if region == "JP":
        return "お世話になっております。" + (f"\n{display}、お疲れさまです。" if display else "")
    if region == "CN":
        return f"您好，{display}：" if display else "您好："
    if region == "AE":
        return f"As-salaam alaikum {display}," if display else "As-salaam alaikum,"
    if region == "BR":
        return f"Olá, {display}, tudo bem?" if display else "Olá, tudo bem?"
    if region == "DE":
        return f"Guten Tag {display}," if display else "Guten Tag,"
    if region == "US":
        return f"Hi {display}," if display else "Hi there,"
    return f"Dear {display}," if display else "Dear colleague,"


class RewriteEngine:
    def __init__(self, index: KnowledgeIndex, settings: Settings | None = None):
        self.index = index
        self.settings = settings or get_settings()

    # -- helpers -----------------------------------------------------------
    def _region_entry(self, region: str, category: str) -> KnowledgeEntry | None:
        for entry in self.index.entries:
            if entry.region == region.upper() and entry.category == category:
                return entry
        return None

    def _has_greeting(self, text: str) -> bool:
        return bool(GREETING_RE.match(text.strip()))

    def _has_closing(self, text: str, region: str) -> bool:
        closing = CLOSINGS.get(region.upper(), "")
        tail = text.strip().lower()[-120:]
        if closing and closing.lower()[:8] in tail:
            return True
        return any(
            word in tail
            for word in ("regards", "thanks", "thank you", "sincerely", "abraço", "よろしく", "谢谢", "best,")
        )

    @staticmethod
    def _apply_spans(text: str, flagged: Iterable[FlaggedSpan]) -> tuple[str, list[str]]:
        replacements = sorted(
            [span for span in flagged if span.suggested_text is not None],
            key=lambda span: span.start,
            reverse=True,
        )
        result = text
        applied: list[str] = []
        for span in replacements:
            if 0 <= span.start < span.end <= len(result):
                result = result[: span.start] + str(span.suggested_text) + result[span.end :]
                applied.append(span.citation_id or "")
        return result, [item for item in applied if item]

    @staticmethod
    def _deflate_urgency(text: str) -> tuple[str, bool]:
        new_text, count = URGENCY_RE.subn("by Friday", text, count=1)
        return new_text, count > 0

    def _entry_ids(self, entries: Iterable[KnowledgeEntry | None]) -> list[str]:
        return [entry.id for entry in entries if entry is not None]

    # -- public API --------------------------------------------------------
    def suggest(
        self,
        text: str,
        region: str,
        flagged: list[FlaggedSpan],
        citations=None,
        receiver_name: str | None = None,
        use_llm: bool | None = None,
    ) -> list[Rewrite]:
        region = region.upper()
        greeting_entry = self._region_entry(region, "greeting")
        formality_entry = self._region_entry(region, "formality")
        directness_entry = self._region_entry(region, "directness")
        context_entries = [greeting_entry, formality_entry, directness_entry]
        context_ids = self._entry_ids(context_entries)

        if use_llm is not False and self.settings.llm_ready:
            llm = self._llm_rewrites(text, region, flagged, context_entries, receiver_name)
            if llm:
                return llm

        softened, applied_ids = self._apply_spans(text, flagged)
        softened, urgency_changed = self._deflate_urgency(softened)
        base_ids = context_ids + applied_ids

        variants: list[Rewrite] = []
        variants.append(
            Rewrite(
                text=softened.strip(),
                rationale=(
                    "Replaced the flagged wording with region-appropriate phrasing"
                    + (" and gave the request a concrete deadline." if urgency_changed else ".")
                ),
                strategy="soften",
                citation_ids=sorted(set(base_ids)),
            )
        )

        greeting = greeting_for(region, receiver_name)
        closing = CLOSINGS.get(region, "Best regards,")
        formal = softened.strip()
        if not self._has_greeting(formal):
            formal = f"{greeting}\n\n{formal}"
        if not self._has_closing(formal, region):
            formal = f"{formal}\n\n{closing}"
        variants.append(
            Rewrite(
                text=formal,
                rationale=(
                    f"Added the greeting and closing shape common in {region} business writing, "
                    "with the flagged wording softened."
                ),
                strategy="formalize",
                citation_ids=sorted(set(base_ids)),
            )
        )

        courtesy = COURTESY.get(region, "")
        localized = formal
        if courtesy and courtesy not in localized:
            localized = f"{localized}\n{courtesy}"
        variants.append(
            Rewrite(
                text=localized,
                rationale=(
                    f"Uses {region}-typical courtesy phrasing from the retrieved etiquette entry; "
                    "keep only what fits your relationship with the recipient."
                ),
                strategy="localize",
                citation_ids=sorted(set(base_ids)),
            )
        )

        seen: set[str] = set()
        unique: list[Rewrite] = []
        for variant in variants:
            key = re.sub(r"\s+", " ", variant.text).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(variant)
        return unique[:3]

    # -- optional LLM path -------------------------------------------------
    def _llm_rewrites(
        self,
        text: str,
        region: str,
        flagged: list[FlaggedSpan],
        entries: list[KnowledgeEntry | None],
        receiver_name: str | None,
    ) -> list[Rewrite] | None:
        snippets = "\n".join(
            f"- ({entry.region}) {entry.title}: {entry.excerpt(280)} Preferred: {'; '.join(entry.preferred[:2])}"
            for entry in entries
            if entry is not None
        )
        if not snippets:
            return None
        flags = "\n".join(f"- {span.text!r}: {span.reason}" for span in flagged[:6]) or "- none"
        prompt = (
            f"Rewrite this business message for a recipient likely in {region}. "
            "Use only the etiquette rules below; do not invent cultural facts. Keep the meaning, "
            "stay in the original language, and return 1-3 options.\n\n"
            f"Etiquette rules:\n{snippets}\n\nFlagged phrases:\n{flags}\n\n"
            f"Message:\n{text}\n\n"
            'Return strict JSON: [{"text": "...", "rationale": "..."}]'
        )
        payload = {
            "model": self.settings.llm_model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a careful cross-cultural business editor. Never stereotype people.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        request = urllib.request.Request(
            f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.llm_api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.llm_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            parsed = _parse_llm_json(content)
        except (urllib.error.URLError, KeyError, ValueError, TimeoutError, OSError):
            return None
        citation_ids = self._entry_ids(entries)
        rewrites: list[Rewrite] = []
        for item in parsed[:3]:
            if isinstance(item, str):
                item = {"text": item, "rationale": f"LLM rewrite grounded in {region} etiquette entries."}
            body = str(item.get("text", "")).strip()
            if not body:
                continue
            rewrites.append(
                Rewrite(
                    text=body,
                    rationale=str(item.get("rationale", "Grounded in retrieved etiquette entries."))[:400],
                    strategy="localize",
                    citation_ids=citation_ids,
                    generated_by=f"llm:{self.settings.llm_model}",
                )
            )
        return rewrites or None


def _parse_llm_json(content: str) -> list:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        content = re.sub(r"\n?```$", "", content).strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "rewrites" in parsed:
            parsed = parsed["rewrites"]
        return list(parsed) if isinstance(parsed, list) else []
    except ValueError:
        # accept numbered lines as a fallback
        lines = [line.strip(" -*\t") for line in content.splitlines() if line.strip()]
        return [line for line in lines if len(line) > 12][:3]
