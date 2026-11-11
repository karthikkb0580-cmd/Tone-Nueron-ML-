"""Command-line entry point for Tone Neuron."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _build_index() -> int:
    from tone_neuron.config import get_settings
    from tone_neuron.knowledge.store import KnowledgeIndex

    settings = get_settings()
    settings.ensure_dirs()
    index = KnowledgeIndex.build(settings=settings)
    index.save(settings.index_dir)
    stats = index.stats()
    print(f"Index built: {stats['entries']} entries across {stats['regions']}")
    print(f"embedder={stats['embedder']}  store={stats['vector_store']}  reranker={stats['reranker']}")
    for region in stats["regions"]:
        hits = index.retrieve("greeting honorifics deadlines", k=2, region=region)
        line = " | ".join(f"{hit.entry.id} ({hit.score:.3f})" for hit in hits)
        print(f"  {region}: {line}")
    print(f"Saved to {settings.index_dir}")
    return 0


def _train(args: argparse.Namespace) -> int:
    from tone_neuron.ml.infer import reset_engine
    from tone_neuron.ml.train import train_all

    metrics = train_all(
        n=args.n,
        seed=args.seed,
        use_transformer=args.transformer,
        transformer_model=args.transformer_model,
    )
    print(f"Dataset: {metrics['dataset']}")
    for task_name, task in metrics["tasks"].items():
        best = task["best"]
        baseline = task["baseline"]
        print()
        print(f"[{task_name}] selected={task['selected']}")
        print(f"  baseline  accuracy={baseline['accuracy']:.3f}  macro_f1={baseline['macro_f1']:.3f}")
        print(f"  best      accuracy={best['accuracy']:.3f}  macro_f1={best['macro_f1']:.3f}")
        print(f"  transformer: {task['transformer'].get('status')} {task['transformer'].get('reason', '')}")
        print("  per region:")
        for region, row in best["per_region"].items():
            print(
                f"    {region}: accuracy={row['accuracy']:.3f} "
                f"macro_f1={row['macro_f1']:.3f} n={row['support']}"
            )
    reset_engine()
    print()
    print("Artifacts written to artifacts/models (metrics.json, *_best.json).")
    return 0


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    from tone_neuron.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "tone_neuron.api.main:app",
        host=args.host or settings.api_host,
        port=args.port or settings.api_port,
        reload=False,
    )
    return 0


def _analyze(args: argparse.Namespace) -> int:
    from tone_neuron.ml.infer import get_engine

    receiver: dict = {}
    if args.name:
        receiver["name"] = args.name
    if args.email:
        receiver["email"] = args.email
    if args.region:
        receiver["region_override"] = args.region
    result = get_engine().analyze(args.text, {"surface": "manual"}, receiver)
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    return 0


def _mascot(args: argparse.Namespace) -> int:
    from tone_neuron.mascot.app import main as mascot_main

    return int(mascot_main([]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tone-neuron",
        description="Tone Neuron — cross-cultural communication assistant",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="run the offline demo")
    sub.add_parser("build-index", help="build the OKF → embeddings index")
    sub.add_parser("mascot", help="launch the desktop mascot (PySide6)")

    train_parser = sub.add_parser("train", help="generate data, train and compare models")
    train_parser.add_argument("--n", type=int, default=2400)
    train_parser.add_argument("--seed", type=int, default=7)
    train_parser.add_argument("--transformer", action="store_true", help="also train DistilBERT/XLM-R")
    train_parser.add_argument("--transformer-model", default="distilbert-base-uncased")

    serve_parser = sub.add_parser("serve", help="run the FastAPI backend")
    serve_parser.add_argument("--host", default=None)
    serve_parser.add_argument("--port", type=int, default=None)

    analyze_parser = sub.add_parser("analyze", help="analyse one message from the terminal")
    analyze_parser.add_argument("text")
    analyze_parser.add_argument("--name", default=None)
    analyze_parser.add_argument("--email", default=None)
    analyze_parser.add_argument("--region", default=None, help="override region, e.g. JP")

    args = parser.parse_args(argv)
    if args.command == "demo":
        from tone_neuron.demo import run_demo

        return run_demo()
    if args.command == "build-index":
        return _build_index()
    if args.command == "train":
        return _train(args)
    if args.command == "serve":
        return _serve(args)
    if args.command == "mascot":
        return _mascot(args)
    if args.command == "analyze":
        return _analyze(args)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
