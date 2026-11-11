"""Gmail adapter (read-only OAuth).

Scopes are deliberately limited to ``gmail.readonly``: Tone Neuron can read drafts and threads but
can never send, delete or modify mail. Message bodies are returned to the caller and are never
written to disk by this module.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Any

from tone_neuron.adapters.base import AdapterInput, combine_thread
from tone_neuron.config import Settings, get_settings
from tone_neuron.schemas import AnalyzeContext, DraftMessage, ReceiverInfo

_ADDR_RE = re.compile(r'(?:"?([^"<]*?)"?\s*)?<([^>]+)>')


class GmailNotConfigured(RuntimeError):
    """Raised when the Google client libraries or OAuth files are missing."""


def _header(headers: list[dict], name: str) -> str | None:
    for header in headers or []:
        if str(header.get("name", "")).lower() == name.lower():
            return str(header.get("value", ""))
    return None


def _decode(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="replace")
    except (ValueError, UnicodeError):
        return ""


def extract_body(payload: dict | None) -> str:
    """Walk a Gmail MIME payload and return the best plain-text body."""
    if not payload:
        return ""
    mime = str(payload.get("mimeType", ""))
    body = payload.get("body", {}) or {}
    data = body.get("data")
    if mime == "text/plain" and data:
        return _decode(str(data))
    if mime == "text/html" and data:
        html = _decode(str(data))
        return re.sub(r"<[^>]+>", " ", html)
    for part in payload.get("parts", []) or []:
        text = extract_body(part)
        if text.strip():
            return text
    if data:
        return _decode(str(data))
    return ""


def addresses(value: str | None) -> list[tuple[str, str]]:
    if not value:
        return []
    found = _ADDR_RE.findall(value)
    if found:
        return [(name.strip() or email.split("@")[0], email.strip()) for name, email in found]
    return [("", part.strip()) for part in value.split(",") if "@" in part]


class GmailClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    # -- auth --------------------------------------------------------------
    def _imports(self):
        try:
            from google.auth.transport.requests import Request  # type: ignore
            from google.oauth2.credentials import Credentials  # type: ignore
            from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
            from googleapiclient.discovery import build  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise GmailNotConfigured(
                "Gmail support needs `pip install -r requirements-optional.txt` "
                "(google-api-python-client, google-auth-oauthlib)."
            ) from exc
        return Request, Credentials, InstalledAppFlow, build

    def credentials(self):
        Request, Credentials, InstalledAppFlow, _ = self._imports()
        scopes = [self.settings.gmail_scopes]
        token_path = Path(self.settings.gmail_token_file).expanduser()
        creds_path = Path(self.settings.gmail_credentials_file).expanduser()
        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            if not creds_path.exists():
                raise GmailNotConfigured(
                    f"OAuth client file not found at {creds_path}. Create a desktop OAuth client in "
                    "Google Cloud and save the JSON there (read-only Gmail scope)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), scopes)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    def service(self):
        _, _, _, build = self._imports()
        return build("gmail", "v1", credentials=self.credentials(), cache_discovery=False)

    # -- reads -------------------------------------------------------------
    def list_drafts(self, max_results: int = 10) -> list[dict]:
        response = (
            self.service()
            .users()
            .drafts()
            .list(userId=self.settings.gmail_user_id, maxResults=max_results)
            .execute()
        )
        return list(response.get("drafts", []))

    def get_draft(self, draft_id: str) -> DraftMessage:
        raw = (
            self.service()
            .users()
            .drafts()
            .get(userId=self.settings.gmail_user_id, id=draft_id, format="full")
            .execute()
        )
        message = raw.get("message", {}) or {}
        payload = message.get("payload", {}) or {}
        headers = payload.get("headers", []) or []
        to_header = _header(headers, "To") or ""
        recipients = addresses(to_header)
        return DraftMessage(
            draft_id=draft_id,
            thread_id=message.get("threadId"),
            to=[email for _, email in recipients],
            subject=_header(headers, "Subject"),
            body=extract_body(payload).strip(),
            snippet=str(message.get("snippet", ""))[:400],
        )

    def get_thread(self, thread_id: str) -> list[str]:
        raw = (
            self.service()
            .users()
            .threads()
            .get(userId=self.settings.gmail_user_id, id=thread_id, format="full")
            .execute()
        )
        bodies: list[str] = []
        for message in raw.get("messages", []) or []:
            text = extract_body(message.get("payload", {})).strip()
            if text:
                bodies.append(text)
        return bodies

    # -- mapping -----------------------------------------------------------
    def draft_to_input(self, draft: DraftMessage, thread_bodies: list[str] | None = None) -> AdapterInput:
        recipient = None
        receiver: ReceiverInfo
        if draft.to:
            recipient = draft.to[0]
        if recipient:
            local = recipient.split("@")[0].replace(".", " ").replace("_", " ").title()
            receiver = ReceiverInfo(name=local, email=recipient)
        else:
            receiver = ReceiverInfo()
        context = AnalyzeContext(
            surface="email_thread" if thread_bodies else "email_draft",
            subject=draft.subject,
            thread_history=thread_bodies or [],
        )
        return AdapterInput(text=draft.body, context=context, receiver=receiver)

    def scan_drafts(self, engine: Any, max_results: int = 5) -> list[tuple[DraftMessage, Any]]:
        """Read drafts and analyse them without persisting any body."""
        results: list[tuple[DraftMessage, Any]] = []
        for item in self.list_drafts(max_results=max_results):
            draft = self.get_draft(item["id"])
            thread = self.get_thread(draft.thread_id) if draft.thread_id else []
            payload = self.draft_to_input(draft, combine_thread(thread) or None)
            analysis = engine.analyze(payload.text, payload.context, payload.receiver)
            results.append((draft, analysis))
        return results
