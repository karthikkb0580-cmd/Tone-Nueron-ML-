"""Frozen-app entry point: run the API in-process, then show the mascot.

Used by the PyInstaller build in ``packaging/ToneNeuron.spec``. Keeping the backend in the same
process means the downloaded app needs no Python install and no separate server.

``--smoke --smoke-out <file>`` starts the backend, calls /health and /analyze, writes a JSON report
and exits without opening a window. CI runs it on every platform to prove the packaged app works.
"""

from __future__ import annotations

import argparse
import json
import logging
import multiprocessing
import os
import socket
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path

APP_DIR = Path.home() / ".tone-neuron"
LOG_FILE = APP_DIR / "app.log"
ERROR_FILE = APP_DIR / "error.log"

if not getattr(sys, "frozen", False):
    # Running from the source tree (local testing / CI smoke): make the package importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _ensure_std_streams() -> None:
    """Windowed builds on Windows have no console: stdout/stderr are None.

    Uvicorn configures its log handlers from ``sys.stderr``; leaving it as None makes the server
    thread fail on startup (and the app look dead). Give every library a writable sink.
    """
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def _configure() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    # The bundle may be read-only; keep the index, models and card state in the user's home.
    os.environ.setdefault("TONE_NEURON_ARTIFACTS_DIR", str(APP_DIR / "artifacts"))
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _free_port(preferred: int = 8000) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])


def _start_backend(port: int):
    import uvicorn

    from tone_neuron.api.main import app

    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
    )
    threading.Thread(target=server.run, name="tone-neuron-api", daemon=True).start()
    return server


def _wait_for_port(port: int, timeout: float = 45.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.4)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.2)
    return False


def _get_json(port: int, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _smoke(port: int, out_path: str) -> int:
    """Prove the packaged backend answers; return 0 on success."""
    report: dict = {"backend_ready": False, "port": port}
    code = 0
    try:
        if not _wait_for_port(port, timeout=90):
            raise RuntimeError(f"backend did not open port {port}")
        report["backend_ready"] = True
        health = _get_json(port, "/health")
        report["health"] = {
            "status": health.get("status"),
            "entries": health.get("knowledge_entries"),
            "embedder": health.get("embedder"),
            "models": health.get("model_loaded"),
        }
        analysis = _get_json(
            port,
            "/analyze",
            {
                "text": "Hey Tanaka, your work on this is useless. Send it now.",
                "context": {"surface": "email_draft"},
                "receiver_info": {"name": "Kenji Tanaka", "email": "k.tanaka@example.co.jp"},
            },
        )
        report["analyze"] = {
            "region": analysis.get("region"),
            "risk": analysis.get("risk"),
            "citations": len(analysis.get("citations", [])),
        }
        if health.get("status") != "ok" or analysis.get("region") != "JP":
            code = 4
            report["error"] = "unexpected health/analyze result"
    except Exception as exc:  # noqa: BLE001 - report whatever happened
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        code = 3
        logging.exception("smoke test failed")
    finally:
        Path(out_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report))
    return code


def _fatal(message: str) -> None:
    """Surface fatal errors even when there is no console."""
    ERROR_FILE.parent.mkdir(parents=True, exist_ok=True)
    ERROR_FILE.write_text(message, encoding="utf-8")
    try:
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                0,
                f"Tone Neuron could not start.\n\n{message[-1500:]}\n\nLog: {ERROR_FILE}",
                "Tone Neuron",
                0x10,
            )
        elif sys.stderr is not None:
            print(message, file=sys.stderr)
    except Exception:  # noqa: BLE001 - never fail while reporting a failure
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tone Neuron desktop app")
    parser.add_argument("--smoke", action="store_true", help="start the API, verify it, exit")
    parser.add_argument("--smoke-out", default="smoke.json", help="smoke report path")
    args, _unknown = parser.parse_known_args(argv or [])

    _ensure_std_streams()
    _configure()
    port = _free_port()
    logging.info("starting backend on 127.0.0.1:%s", port)
    _start_backend(port)

    if args.smoke:
        return _smoke(port, args.smoke_out)

    ready = _wait_for_port(port)
    logging.info("backend ready=%s on 127.0.0.1:%s", ready, port)

    from tone_neuron.mascot.app import main as mascot_main

    return int(mascot_main(["--backend", f"http://127.0.0.1:{port}"]))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - frozen windowed apps have no console
        _fatal(traceback.format_exc())
        sys.exit(1)
