"""FastAPI dependencies (process-wide singletons)."""

from __future__ import annotations

from functools import lru_cache

from tone_neuron.cards import CardBook
from tone_neuron.coaching import SessionStore
from tone_neuron.ml.infer import NeuroEngine, get_engine


@lru_cache(maxsize=1)
def get_session_store() -> SessionStore:
    return SessionStore()


def get_engine_dep() -> NeuroEngine:
    return get_engine()


@lru_cache(maxsize=1)
def get_cards() -> CardBook:
    return get_engine().cards
