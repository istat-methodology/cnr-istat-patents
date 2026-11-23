#!/usr/bin/env python3
"""Control 2 - how much cross-model agreement is there, relative to what is possible?

The ARI between two models is bounded by how reproducible each model's own
clustering is (ARI between K-means seeds). This control divides each pairwise ARI
by the geometric mean of the two seed-ARIs (the noise ceiling) and ranks the models
by how much they agree with all the others.

Reads : assignments and seed_stability_ari.csv written by step 2.
Output: controls/c02_cross_model_pairs.csv       one row per pair, cohort, K
        controls/c02_cross_model_summary.csv     one row per model, cohort, K
        controls/c02_matrix_<cohort>_k<K>.csv    square ARI matrix (raw)
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score as ari

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    args = parser.parse_args()
    cfg = common.load_config(args.config)
    run = common.run_dir(cfg, args.quick)
    common.read_run_info(run)
    folder = run / "controls"
    folder.mkdir(parents=True, exist_ok=True)

    seed_ari = pd.read_csv(run / "metrics" / "seed_stability_ari.csv")
    noise = seed_ari.groupby(["cohort", "model", "k"])["ARI"].mean().rename("seed_ari").reset_index()

    pair_rows, summary_rows = [], []
    for cohort in cfg["cohorts"]:
        files = {m: p for c, m, p in common.assignment_files(run) if c == cohort}
        data = {m: pd.read_parquet(p) for m, p in files.items()}
        ids = next(iter(data.values()))["publication_number"].astype(str)
        for m, a in data.items():
            if not a["publication_number"].astype(str).equals(ids):
                raise ValueError(f"{m}: assignment order differs from the others")
        for k in cfg["k"]:
            col = f"cluster_k{k}"
            models = list(data)
            matrix = pd.DataFrame(np.eye(len(models)), index=models, columns=models)
            level = noise[(noise.cohort == cohort) & (noise.k == k)].set_index("model")["seed_ari"]
            for a, b in itertools.combinations(models, 2):
                value = ari(data[a][col], data[b][col])
                matrix.loc[a, b] = matrix.loc[b, a] = value
                ceiling = float(np.sqrt(level[a] * level[b]))
                pair_rows.append({"cohort": cohort, "k": k, "model_a": a, "model_b": b,
                                  "ARI": value, "noise_ceiling": ceiling,
                                  "ARI_over_ceiling": value / ceiling})
            matrix.to_csv(folder / f"c02_matrix_{cohort}_k{k}.csv")
            for m in models:
                others = [x for x in models if x != m]
                embedding_others = [x for x in others if common.kind_of(x) == "embedding"]
                summary_rows.append({
                    "cohort": cohort, "k": k, "model": m, "kind": common.kind_of(m),
                    "seed_ari": level[m],
                    "mean_ari_vs_others": matrix.loc[m, others].mean(),
                    "mean_ari_vs_embedding_models": matrix.loc[m, embedding_others].mean(),
                    "max_ari": matrix.loc[m, others].max(),
                    "closest_model": matrix.loc[m, others].idxmax(),
                })
    pairs = pd.DataFrame(pair_rows)
    summary = pd.DataFrame(summary_rows)
    pairs.to_csv(folder / "c02_cross_model_pairs.csv", index=False)
    summary.to_csv(folder / "c02_cross_model_summary.csv", index=False)
    print(summary[summary.cohort == "full"].round(3).to_string(index=False))
    print(f"wrote {folder}")


if __name__ == "__main__":
    main()
