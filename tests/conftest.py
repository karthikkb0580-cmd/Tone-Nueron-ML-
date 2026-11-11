from __future__ import annotations

import pytest

from tone_neuron.config import get_settings
from tone_neuron.ml.infer import get_engine, reset_engine


@pytest.fixture(scope="session")
def engine():
    settings = get_settings()
    settings.ensure_dirs()
    reset_engine()
    return get_engine(settings)


@pytest.fixture(scope="session")
def client(engine):
    from fastapi.testclient import TestClient

    from tone_neuron.api.main import app

    with TestClient(app) as test_client:
        yield test_client
