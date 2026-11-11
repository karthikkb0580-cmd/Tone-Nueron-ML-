#!/usr/bin/env python
"""Run the Tone Neuron demo (offline, no API key needed)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tone_neuron.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["demo"]))
