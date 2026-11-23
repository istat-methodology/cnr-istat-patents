#!/usr/bin/env python3
"""Step 2 - K-means for every model, cohort, K and seed (analysis/run_analysis.py).

This step does not re-implement anything: it calls the analysis engine with the
settings of config.yaml and writes everything in <output_dir>/<run_name>/
(metrics, assignments, cluster cards, audit). If that folder already exists the
engine resumes it, so an interrupted run can be restarted with the same command.

--quick: first draws a random sample of publications and runs on that.
         Same code, same settings, minutes instead of an hour. Not a result.
--dry-run: print the engine command and stop.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def make_quick_inputs(cfg: dict, folder: Path) -> tuple[Path, Path]:
    """Subset of the corpus and of every embedding matrix, in the engine's layout."""
    q = cfg["quick"]
    corpus = pd.read_parquet(cfg["data"])
    sample = corpus.sample(n=min(q["n_publications"], len(corpus)), random_state=q["seed"])
    sample = sample.sort_index()
    data_path = folder / "patents_quick.parquet"
    emb_root = folder / "embeddings"
    folder.mkdir(parents=True, exist_ok=True)
    sample.to_parquet(data_path, index=False)
    for model in cfg["models"]:
        src = cfg["embeddings_dir"] / model
        ids = pd.read_parquet(src / "ids.parquet")
        positions = pd.Index(ids["publication_number"]).get_indexer(sample["publication_number"])
        if (positions < 0).any():
            raise ValueError(f"{model}: some sampled publications are missing from ids.parquet")
        matrix = np.load(src / "embeddings.npy", mmap_mode="r")[positions]
        out = emb_root / model
        out.mkdir(parents=True, exist_ok=True)
        np.save(out / "embeddings.npy", np.asarray(matrix))
        ids.iloc[positions].reset_index(drop=True).to_parquet(out / "ids.parquet", index=False)
    print(f"quick inputs: {len(sample):,} publications in {folder}")
    return data_path, emb_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    parser.add_argument("--dry-run", action="store_true", help="Print the engine command and stop")
    args = parser.parse_args()
    cfg = common.load_config(args.config)

    run = common.run_dir(cfg, args.quick)
    data_path, emb_root = cfg["data"], cfg["embeddings_dir"]
    if args.quick and not args.dry_run:
        data_path, emb_root = make_quick_inputs(cfg, cfg["output_dir"] / (common.run_name(cfg, True) + "-input"))
    elif args.quick:
        data_path = cfg["output_dir"] / (common.run_name(cfg, True) + "-input") / "patents_quick.parquet"
        emb_root = data_path.parent / "embeddings"

    command = [
        sys.executable, str(common.REPO / "analysis" / "run_analysis.py"),
        "--data", str(data_path),
        "--concordance", str(cfg["concordance"]),
        "--embeddings-dir", str(emb_root),
        "--models", *cfg["models"],
        "--cohorts", *cfg["cohorts"],
        "--k", *map(str, cfg["k"]),
        "--seeds", *map(str, cfg["seeds"]),
        "--n-init", str(cfg["n_init"]),
        "--max-iter", str(cfg["max_iter"]),
        "--threads", str(cfg["threads"]),
        "--silhouette-sample", str(cfg["silhouette_sample"]),
    ]
    resume = (run / "run_config.json").exists()
    if resume:
        command += ["--resume-dir", str(run)]
    else:
        command += ["--output-dir", str(run.parent), "--run-name", run.name]
    print(("resuming " if resume else "starting ") + str(run))
    print(" ".join(command))
    if args.dry_run:
        return

    subprocess.run(command, check=True)
    info = {
        "run": run.name,
        "quick": args.quick,
        "data": str(data_path),
        "concordance": str(cfg["concordance"]),
        "embeddings_dir": str(emb_root),
        "models": cfg["models"],
        "cohorts": cfg["cohorts"],
        "k": cfg["k"],
        "seeds": cfg["seeds"],
    }
    (run / "paper_run.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print("step 2 done")


if __name__ == "__main__":
    main()
