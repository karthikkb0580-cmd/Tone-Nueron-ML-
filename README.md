# 🧠 Tone Neuron — *Detect and Protect*

Tone Neuron is a cross-cultural communication assistant with a desktop-pet mascot. It reads
Gmail drafts/threads and meeting transcripts, infers the **receiver's likely cultural region**,
scores how risky the sender's wording is *for that receiver*, blocks only the genuinely rude or
sensitive messages, and coaches the sender at the end of the day.

> Culture is a **soft signal**, never a verdict about a person. Every verdict is a guess with a
> confidence score, every verdict cites the etiquette entry behind it, and the user can always
> override the detected region. See [docs/FAIRNESS.md](docs/FAIRNESS.md).

```
        ┌──────────────────────────────┐
        │   Neuro (PySide6 desktop pet)│  idle / alert / thinking / happy / worried
        │   draggable · snaps to edge  │
        └──────────────┬───────────────┘
                       │ HTTP (localhost)
┌──────────────────────▼─────────────────────────────────────────────┐
│ FastAPI  /analyze  /gate  /coaching/daily  /cards  /health         │
│                                                                    │
│  ┌──────────────┐   ┌───────────────────┐   ┌────────────────────┐ │
│  │  Adapters    │   │   ML inference    │   │   Knowledge (RAG)  │ │
│  │  gmail.py    │──▶│ A culture infer   │◀─▶│ OKF files per      │ │
│  │  meeting.py  │   │ B tone/risk       │   │ region + embedder  │ │
│  │  chat/text   │   │ C grounded rewrite│   │ + MMR + reranker   │ │
│  └──────────────┘   └───────────────────┘   └────────────────────┘ │
│         │                     │                       │            │
│         └────────▶ Gate (block / hint / allow) ───────┘            │
│                       │                                            │
│                 Session store (in-memory, redacted, TTL)           │
│                       │                                            │
│                 Coaching review + culture cards                    │
└────────────────────────────────────────────────────────────────────┘
```

## What is built (and only this)

| # | Feature | Where |
|---|---------|-------|
| 1 | **Receiver-Culture Checker** — region + confidence, region-fit scoring, flagged spans, reasons, 1–3 rewrites, citations | `tone_neuron/ml/infer.py`, `tone_neuron/knowledge/` |
| 2 | **Pre-Send Gate** — high risk ⇒ block + mascot verification; medium/low ⇒ gentle hint; calls ⇒ non-blocking side alert | `tone_neuron/gate.py` |
| 3 | **End-of-day Coaching** — themes, language-fluency micro-lessons, meeting work-culture corrections | `tone_neuron/coaching.py` |
| — | Desktop mascot "Neuro" + per-language characters & collectible culture cards | `tone_neuron/mascot/`, `tone_neuron/data/cards.json` |

## Quick start

```bash
python3.11 -m venv .venv && source .venv/bin/activate      # 3.11+ (tested on 3.11 & 3.12)
pip install -r requirements.txt

cp .env.example .env

# 1) build the knowledge index (OKF -> embeddings -> vector store)
python scripts/build_index.py

# 2) generate the synthetic dataset + train + compare models (writes artifacts/metrics.json)
python scripts/train_models.py

# 3) run the backend
uvicorn tone_neuron.api.main:app --reload --port 8000

# 4) one-shot demo (analyze / gate / coaching / cards, prints citations)
python scripts/demo.py

# 5) the desktop pet (needs a display; PySide6)
pip install -r requirements-optional.txt      # includes PySide6-Essentials
python -m tone_neuron.mascot.app              # GUI
python -m tone_neuron.mascot.app --selftest   # headless state/character check
```

Everything also runs through one CLI: `python -m tone_neuron.cli {demo,build-index,train,serve,mascot,analyze}`.

python -m tone_neuron.mascot.app
```

Tests: `pytest -q` (ML API, gate logic, retrieval).

Optional extras are genuinely optional — the code degrades gracefully:

* `fasttext-wheel` → real FastText baseline. Without it, a **hash n-gram SGD classifier** with the
  same features is used (documented as a FastText-style baseline).
* `sentence-transformers` → dense embeddings. Without it, a deterministic **hashed n-gram embedder**.
* `faiss-cpu` / `qdrant-client` → ANN stores. Without them, an exact **numpy cosine store**.
* `transformers`+`torch` → DistilBERT/XLM-R training. Without them, training skips Task-B transformer
  and says so; the baseline still trains and the best *available* model is saved.
* Any OpenAI-compatible LLM (`TONE_NEURON_LLM_BASE_URL`, `TONE_NEURON_LLM_API_KEY`) → LLM rewrites.
  Without it, a **grounded template rewriter** uses the retrieved entries' preferred phrasing, so
  rewrites are still region-appropriate and cited.

## Architecture (text diagram)

```
Gmail API ─┐                                  ┌─ OKF loader (YAML front matter + prose)
           ├─▶ adapters/*.py ──▶ AnalyzeInput ─┤
captions ──┘   (normalise, never persist)     └─▶ KnowledgeIndex
                                                    │ embedder: st | hashing
                                                    │ store:    faiss | qdrant | numpy
                                                    │ retrieval: hybrid → MMR → rerank
                                                    ▼
                                          citations + region evidence
                                                    │
   analyze(text, context, receiver_info)            ▼
   ├─ Task A  RegionInference   (lexical/identity features → probability distribution)
   ├─ Task B  RiskClassifier    (tone label + risk, conditioned on receiver region)
   ├─ Flags   phrase/cue scanning against retrieved entries
   └─ Task C  Rewriter          (LLM if key else grounded templates)
                                                    │
                                                    ▼
                                            {region, confidence, risk,
                                             flagged_spans, reasons,
                                             rewrites, citations}
```

## Verified results (this environment)

Run on 2026-11-11 inside the project VM: Python 3.12, NumPy 2.5.4, scikit-learn 1.9.1,
fastText 0.9.2, 2,400 synthetic samples (300 per region, 480 per tone), 600 held-out.

| Task | Selected model | Accuracy | Macro-F1 | Hard subset (147/600) |
|---|---|---|---|---|
| A. Region inference (8 classes) | FastText supervised | 1.000 | 1.000 | 1.000 / 1.000 |
| B. Tone + risk (5 classes) | FastText supervised | 1.000 | 1.000 | 1.000 / 1.000 |

Per-region accuracy / macro-F1 and per-class precision / recall / F1 are written to
`artifacts/models/metrics.json` (`tasks.*.best.per_region`, `tasks.*.best.per_class`).

**Read these numbers carefully.** They measure *separability of the synthetic templates*, not
real-world accuracy. The "hard subset" (dropped language/time zone, generic inboxes, diaspora
names) still scores 1.000 because the remaining identity tokens and tone phrases separate the
generated templates. Treat the table as a pipeline check and an upper bound; consented,
human-annotated per-region data is required before any accuracy claim (see `docs/FAIRNESS.md`).

**Transformer comparison.** `DistilBERT`/`XLM-R` training is implemented in
`tone_neuron/ml/transformer_model.py` and enabled with `--transformer`. `torch`/`transformers` are
not installed here, so `metrics.json` records `"status": "skipped"`; the trainer automatically
selects the best macro-F1 across available models and writes `*_best.json` for inference.

**Tests.** `22 passed` with `pytest -q`: ML contract, gate decisions (block / hint / allow /
non-intrusive call alert) and retrieval + citations.

**Desktop mascot.** The PySide6 app is complete, but this VM is headless and missing
`libxkbcommon`, `libEGL`, `freetype` and `fontconfig`, with no root to install them, so the GUI was
**not launched or visually verified here**. It compiles, and `--selftest` exercises every state and
language offscreen on a normal desktop.

**NumPy note.** `fasttext-wheel`'s Python `predict` breaks on NumPy 2 (`np.array(..., copy=False)`).
The baseline calls the C++ predictor directly, which returns the same labels/probabilities without
that conversion, so training and inference work on NumPy 1.x and 2.x.

## Using the API

```bash
curl -s localhost:8000/analyze -H 'content-type: application/json' -d '{
  "text": "Hey Tanaka, send me the report ASAP. This is the third time.",
  "context": {"surface": "email_draft"},
  "receiver_info": {"name": "Kenji Tanaka", "email": "k.tanaka@example.co.jp"}
}' | python -m json.tool
```

```python
from tone_neuron.ml.infer import analyze
out = analyze(text, context={"surface": "meeting"}, receiver_info={"name": "Ana Souza"})
```

Same call for Gmail text and meeting transcripts — only the adapter differs
(`tone_neuron/adapters/gmail.py`, `tone_neuron/adapters/meeting.py`).

Endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /analyze` | Feature 1 verdict (region, risk, spans, reasons, rewrites, citations) |
| `POST /gate` | Feature 2 decision; `sender_confirmed` or `chosen_rewrite_index` releases a block |
| `POST /coaching/daily` | Feature 3 review for the day's checked emails/calls |
| `GET  /cards` | Culture cards + unlock state (`?region=JP` to filter) |
| `GET  /health` | Liveness + which embedder/store/model are active |

## Privacy

* Email/meeting text is processed **in memory** and never written to disk by the backend.
* The session store keeps at most `TONE_NEURON_MAX_EVENTS` redacted excerpts (`a***@x.com`,
  phone digits masked) for the daily review, and `POST /coaching/daily` clears them.
* No content is logged; only counts, region codes and risk labels.
* Gmail credentials live in `.env` / `~/.tone-neuron/` — never in the repo.

## Assumptions (made without blocking on questions)

1. **Region = coarse cultural region**, not nationality. The label set is `JP, IN, DE, US, UK, CN, BR, AE`
   (8 regions, the seed set), extendable by dropping another OKF file into `tone_neuron/data/knowledge/`.
2. **Culture is probabilistic.** Region inference combines name/script priors, email TLD, language,
   timezone, signature and phrasing. Output is capped at 0.95 confidence and always labelled
   *guess*; a user override short-circuits inference (`receiver_info.region_override`).
3. **Task B is conditioned on region** by including region tokens in the feature space and by
   applying per-region calibration/priors; the model is trained on synthetic data, so its metrics
   measure *learnability of the synthetic signal*, not real-world accuracy. Real deployment needs
   consented, human-reviewed data.
4. **"Blocking" is a UI-level gate, not an SMTP-level block.** The backend returns
   `decision="block"`; the Gmail/chat integration is expected to refuse to send until the mascot
   verification returns `allow`. Gmail send is intentionally **not** implemented (read-only OAuth
   scope: `gmail.readonly`), so Tone Neuron can never send mail on its own.
5. **Meetings** start from a transcript file adapter plus a `LiveCaptionSource` stub (a queue you can
   push caption lines into); no meeting SDK is bundled.
6. **LLM rewrites** are optional. The default grounded rewriter is deterministic and offline so the
   project runs with no keys. LLM calls, when enabled, only ever receive the text plus the retrieved
   etiquette snippets, and are told not to invent cultural rules.
7. **Desktop mascot** targets PySide6 on a normal desktop session. In a headless VM it is verified
   with `python -m tone_neuron.mascot.app --selftest` (Qt offscreen), not visually.
8. **Art** is placeholder: emoji/glyph sprites generated from `characters.json` and cached as PNGs in
   `artifacts/mascot/`, designed to be swapped for real PNGs by editing the JSON `sprite` paths.
9. **No persistent user database.** Cards/unlock state and the session store are local JSON/in-memory.
10. Python 3.11 is the declared target; everything also runs on 3.12.

## Layout

```
tone_neuron/
  config.py schemas.py gate.py coaching.py cards.py cli.py
  knowledge/   okf.py (OKF parser) embeddings.py store.py (MMR + rerank)
  ml/          dataset.py features.py baseline_fasttext.py transformer_model.py
               train.py infer.py rewrites.py region_inference.py
  adapters/    base.py gmail.py meeting.py
  api/         main.py deps.py
  mascot/      app.py backend_client.py sprites.py
  data/        knowledge/*.okf.md   characters.json   cards.json
scripts/       build_index.py train_models.py demo.py
tests/         test_api.py test_gate.py test_retrieval.py
docs/          FAIRNESS.md  OKF.md
```

See [docs/OKF.md](docs/OKF.md) for the knowledge-file format.
