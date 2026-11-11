"""Frozen-app entry point: run the API in-process, then show the mascot.

Used by the PyInstaller build in ``packaging/ToneNeuron.spec``. Keeping the backend in the same
process means the downloaded app needs no Python install and no separate server.
"""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import traceback
from pathlib import Path

APP_DIR = Path.home() / ".tone-neuron"
LOG_FILE = APP_DIR / "app.log"


def _configure() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    # The bundle is read-only; keep the index, models and card state in the user's home.
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


def main() -> int:
    _configure()
    port = _free_port()
    _start_backend(port)
    ready = _wait_for_port(port)
    logging.info("backend ready=%s on 127.0.0.1:%s", ready, port)

    from tone_neuron.mascot.app import main as mascot_main

    return int(mascot_main(["--backend", f"http://127.0.0.1:{port}"]))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - frozen apps have no console; leave a trace
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.write_text(traceback.format_exc(), encoding="utf-8")
        raise
