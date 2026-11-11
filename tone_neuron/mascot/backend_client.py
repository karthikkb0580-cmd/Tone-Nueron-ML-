"""Tiny stdlib HTTP client for the local Tone Neuron backend (no extra dependency)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class BackendUnavailable(RuntimeError):
    """The local backend is not running or refused the request."""


class BackendClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 8.0):
        self.base_url = (base_url or "http://127.0.0.1:8000").rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict | None = None) -> Any:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise BackendUnavailable(f"{method} {path}: {exc}") from exc

    def health(self) -> dict:
        return self._request("GET", "/health")

    def analyze(self, text: str, receiver: dict | None = None, surface: str = "email_draft") -> dict:
        return self._request(
            "POST",
            "/analyze",
            {
                "text": text,
                "context": {"surface": surface},
                "receiver_info": receiver or {},
            },
        )

    def gate(self, payload: dict) -> dict:
        return self._request("POST", "/gate", payload)

    def gate_text(self, text: str, channel: str = "email", receiver: dict | None = None) -> dict:
        surface = "meeting" if channel == "call" else "email_draft"
        return self.gate(
            {
                "text": text,
                "context": {"surface": surface},
                "receiver_info": receiver or {},
                "channel": channel,
            }
        )

    def coaching(self, **kwargs) -> dict:
        return self._request("POST", "/coaching/daily", kwargs or {})

    def cards(self, region: str | None = None) -> dict:
        suffix = f"?region={region}" if region else ""
        return self._request("GET", f"/cards{suffix}")
