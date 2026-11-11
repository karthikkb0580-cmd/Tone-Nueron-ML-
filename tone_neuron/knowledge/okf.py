"""OKF (Open Knowledge Format) loader.

See ``docs/OKF.md`` for the format. One file per region; every entry becomes a retrievable,
citable knowledge record.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Literal

import yaml

from tone_neuron.schemas import RiskLevel

MatchMode = Literal["literal", "regex"]

REGION_RE = re.compile(r"^[A-Z]{2,3}$")
ENTRY_ID_RE = re.compile(r"^[a-z]{2,3}\.[a-z0-9_.-]+$")
SECTION_RE = re.compile(r"^##\s+(\S+)\s*$", re.MULTILINE)
RISK_ORDER: dict[str, int] = {"low": 0, "medium": 1, "high": 2}


class OkfError(ValueError):
    """Raised when a knowledge file is malformed (fail loudly at load time)."""


@dataclass(slots=True)
class FlagRule:
    """A phrasing pattern that is risky in this region's business context."""

    pattern: str
    why: str = ""
    severity: RiskLevel = "medium"
    suggested: str | None = None
    match: MatchMode = "literal"
    category: str = ""
    _compiled: re.Pattern[str] | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.severity not in RISK_ORDER:
            raise OkfError(f"invalid severity {self.severity!r} for pattern {self.pattern!r}")
        if not self.pattern.strip():
            raise OkfError("empty flag pattern")
        if self.match == "regex":
            try:
                self._compiled = re.compile(self.pattern, re.IGNORECASE | re.UNICODE)
            except re.error as exc:  # pragma: no cover - config error
                raise OkfError(f"invalid regex {self.pattern!r}: {exc}") from exc
        else:
            self._compiled = re.compile(
                r"(?<!\w)" + re.escape(self.pattern) + r"(?!\w)",
                re.IGNORECASE | re.UNICODE,
            )

    def finditer(self, text: str) -> Iterator[re.Match[str]]:
        if self._compiled is None:  # pragma: no cover - defensive
            return iter(())
        return self._compiled.finditer(text)


@dataclass(slots=True)
class KnowledgeEntry:
    id: str
    region: str
    region_name: str
    title: str
    category: str
    severity: RiskLevel
    tags: list[str]
    guidance: str
    dos: list[str]
    donts: list[str]
    preferred: list[str]
    flags: list[FlagRule]
    caveat: str
    sources: list[str]
    path: str
    language: str | None = None

    def embed_text(self) -> str:
        parts = [
            f"{self.region_name} ({self.region}) {self.category}: {self.title}.",
            self.guidance,
        ]
        if self.dos:
            parts.append("Do: " + "; ".join(self.dos))
        if self.donts:
            parts.append("Avoid: " + "; ".join(self.donts))
        if self.preferred:
            parts.append("Preferred phrasing: " + "; ".join(self.preferred))
        if self.tags:
            parts.append("Tags: " + ", ".join(self.tags))
        return " ".join(p for p in parts if p).strip()

    def excerpt(self, max_chars: int = 320) -> str:
        text = re.sub(r"\s+", " ", self.guidance).strip()
        if len(text) > max_chars:
            text = text[: max_chars - 1].rstrip() + "…"
        return text


@dataclass(slots=True)
class OkfDocument:
    path: Path
    region: str
    region_name: str
    languages: list[str]
    caveat: str
    last_reviewed: str | None
    provenance: dict
    entries: list[KnowledgeEntry]


def _normalise(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [_normalise(item) for item in value if _normalise(item)]
    return [_normalise(value)]


def _split_front_matter(text: str, path: Path) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise OkfError(f"{path}: OKF file must start with a '---' front-matter block")
    lines = text.splitlines()
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        raise OkfError(f"{path}: unterminated YAML front matter")
    raw = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :])
    try:
        meta = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise OkfError(f"{path}: invalid YAML front matter: {exc}") from exc
    if not isinstance(meta, dict):
        raise OkfError(f"{path}: front matter must be a mapping")
    return meta, body


def _body_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(body))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        content = re.sub(r"^#{3,}\s*(Guidance|Notes?)\s*$", "", content, flags=re.MULTILINE)
        sections[match.group(1).strip()] = content.strip()
    return sections


def load_okf_file(path: str | Path) -> OkfDocument:
    path = Path(path)
    meta, body = _split_front_matter(path.read_text(encoding="utf-8"), path)

    region = str(meta.get("region", "")).strip().upper()
    if not REGION_RE.match(region):
        raise OkfError(f"{path}: 'region' must be a 2-3 letter code, got {region!r}")
    region_name = _normalise(meta.get("region_name")) or region
    languages = _as_list(meta.get("languages") or meta.get("language"))
    caveat = _normalise(meta.get("caveat"))
    provenance = meta.get("provenance") or {}
    if not isinstance(provenance, dict):
        provenance = {"note": _normalise(provenance)}
    sections = _body_sections(body)

    raw_entries = meta.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise OkfError(f"{path}: 'entries' must be a non-empty list")

    entries: list[KnowledgeEntry] = []
    seen: set[str] = set()
    for raw in raw_entries:
        if not isinstance(raw, dict):
            raise OkfError(f"{path}: every entry must be a mapping")
        entry_id = str(raw.get("id", "")).strip()
        if not ENTRY_ID_RE.match(entry_id):
            raise OkfError(f"{path}: invalid entry id {entry_id!r}")
        if not entry_id.startswith(f"{region.lower()}."):
            raise OkfError(f"{path}: entry {entry_id!r} must start with '{region.lower()}.'")
        if entry_id in seen:
            raise OkfError(f"{path}: duplicate entry id {entry_id!r}")
        seen.add(entry_id)

        severity = str(raw.get("severity", "medium")).lower()
        if severity not in RISK_ORDER:
            raise OkfError(f"{path}: entry {entry_id} has invalid severity {severity!r}")

        flags: list[FlagRule] = []
        for flag in raw.get("flagged") or []:
            if not isinstance(flag, dict) or not flag.get("pattern"):
                raise OkfError(f"{path}: entry {entry_id} has a malformed 'flagged' item")
            flag_severity = str(flag.get("severity", severity)).lower()
            flags.append(
                FlagRule(
                    pattern=str(flag["pattern"]),
                    why=_normalise(flag.get("why")),
                    severity=flag_severity,  # type: ignore[arg-type]
                    suggested=_normalise(flag.get("suggested")) or None,
                    match=str(flag.get("match", "literal")).lower(),  # type: ignore[arg-type]
                    category=_normalise(flag.get("category")) or str(raw.get("category", "")),
                )
            )

        guidance = sections.get(entry_id, "").strip() or _normalise(raw.get("guidance"))
        entries.append(
            KnowledgeEntry(
                id=entry_id,
                region=region,
                region_name=region_name,
                title=_normalise(raw.get("title")) or entry_id,
                category=_normalise(raw.get("category")) or "general",
                severity=severity,  # type: ignore[arg-type]
                tags=_as_list(raw.get("tags")),
                guidance=guidance,
                dos=_as_list(raw.get("do") or raw.get("dos")),
                donts=_as_list(raw.get("avoid") or raw.get("donts")),
                preferred=_as_list(raw.get("preferred")),
                flags=flags,
                caveat=caveat,
                sources=_as_list(raw.get("cites")) or _as_list(provenance.get("sources")),
                path=str(path),
                language=languages[0] if languages else None,
            )
        )

    return OkfDocument(
        path=path,
        region=region,
        region_name=region_name,
        languages=languages,
        caveat=caveat,
        last_reviewed=str(meta.get("last_reviewed")) if meta.get("last_reviewed") else None,
        provenance=provenance,
        entries=entries,
    )


def load_okf_dir(directory: str | Path) -> list[OkfDocument]:
    directory = Path(directory)
    if not directory.exists():
        raise OkfError(f"knowledge directory not found: {directory}")
    docs = [load_okf_file(path) for path in sorted(directory.glob("*.okf.md"))]
    if not docs:
        raise OkfError(f"no *.okf.md files in {directory}")
    regions = [doc.region for doc in docs]
    duplicates = {r for r in regions if regions.count(r) > 1}
    if duplicates:
        raise OkfError(f"duplicate region profiles: {sorted(duplicates)}")
    return docs


def load_entries(directory: str | Path) -> list[KnowledgeEntry]:
    return [entry for doc in load_okf_dir(directory) for entry in doc.entries]


def corpus_fingerprint(entries: Iterable[KnowledgeEntry]) -> str:
    payload = json.dumps(
        [[entry.id, entry.embed_text()] for entry in entries],
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
