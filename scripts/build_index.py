#!/usr/bin/env python
"""Build the OKF knowledge index: parse → embed → vector store → save cache."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tone_neuron.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["build-index"]))
