"""Tone Neuron FastAPI backend."""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from tone_neuron.api.deps import get_engine_dep, get_session_store
from tone_neuron.coaching import SessionStore, build_daily_review
from tone_neuron.config import get_settings
from tone_neuron.gate import evaluate_gate
from tone_neuron.ml.infer import NeuroEngine
from tone_neuron.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CardsResponse,
    CoachingRequest,
    CoachingResponse,
    GateRequest,
    GateResponse,
    HealthResponse,
)

settings = get_settings()
START_TIME = time.time()

app = FastAPI(
    title="Tone Neuron",
    version=settings.version,
    description=(
        "Cross-cultural communication assistant: receiver-culture check, pre-send gate and "
        "end-of-day coaching. Content is processed in memory and never stored permanently."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _model_version() -> str:
    metrics_path = Path(settings.model_dir) / "metrics.json"
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            return f"trained:{metrics.get('generated_at', 'unknown')}"
        except (OSError, ValueError):
            pass
    return "rules/heuristic"


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health(engine: NeuroEngine = Depends(get_engine_dep)) -> HealthResponse:
    stats = engine.index.stats()
    return HealthResponse(
        status="ok",
        version=settings.version,
        embedder=str(stats["embedder"]),
        vector_store=str(stats["vector_store"]),
        reranker=str(stats["reranker"]),
        knowledge_entries=int(stats["entries"]),
        regions=list(stats["regions"]),
        model_loaded=engine.tone_model.model is not None or engine.region_model.classifier is not None,
        model_version=_model_version(),
        llm_enabled=settings.llm_ready,
        uptime_seconds=round(time.time() - START_TIME, 2),
    )


@app.post("/analyze", response_model=AnalyzeResponse, tags=["feature-1"])
def analyze_endpoint(
    request: AnalyzeRequest,
    engine: NeuroEngine = Depends(get_engine_dep),
    store: SessionStore = Depends(get_session_store),
) -> AnalyzeResponse:
    """Receiver-culture check: region + confidence, risk, flagged spans, reasons, rewrites, citations."""
    try:
        analysis = engine.analyze(request.text, request.context, request.receiver_info)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    store.record(analysis, channel="email" if request.context.surface != "meeting" else "call")
    return analysis


@app.post("/gate", response_model=GateResponse, tags=["feature-2"])
def gate_endpoint(
    request: GateRequest,
    engine: NeuroEngine = Depends(get_engine_dep),
    store: SessionStore = Depends(get_session_store),
) -> GateResponse:
    """Pre-send gate: block only high-risk rude/sensitive content; calls get a side alert only."""
    analysis = engine.analyze(request.text, request.context, request.receiver_info)
    store.record(analysis, channel=request.channel)
    return evaluate_gate(analysis, request)


@app.post("/coaching/daily", response_model=CoachingResponse, tags=["feature-3"])
def coaching_endpoint(
    request: CoachingRequest | None = None,
    engine: NeuroEngine = Depends(get_engine_dep),
    store: SessionStore = Depends(get_session_store),
) -> CoachingResponse:
    """End-of-day review of the checked emails and calls, with citations."""
    return build_daily_review(store, engine.index, engine.cards, request or CoachingRequest())


@app.get("/cards", response_model=CardsResponse, tags=["cards"])
def cards_endpoint(
    region: str | None = Query(default=None, min_length=2, max_length=3),
    engine: NeuroEngine = Depends(get_engine_dep),
) -> CardsResponse:
    """Collectible culture cards and unlock state."""
    return engine.cards.cards(region)
