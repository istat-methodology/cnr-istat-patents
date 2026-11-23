#!/usr/bin/env python3
"""Control 3 - is the Chinese-office (CN) share a confounder, or just a smaller sample?

CN is 67.8% of the corpus. Removing it changes the clustering (ARI full vs no-CN is
0.40-0.88). That alone does not show a confounder: refitting K-means on any 20,579
patents would also move the clusters a little. So two parts:

A. Removal test (c03_cn_vs_random.csv). Per model and K, same K-means settings:
   - remove-CN       the exclude-cn clustering of step 2
   - remove-random-i the same number of patents removed at random from the full corpus (config: random_removal_draws)
   Columns: ARI between the full clustering (restricted to the kept patents) and the refit,
   and AMI vs WIPO before and after. If remove-CN moves the clusters or the AMI much more
   than remove-random, CN is a confounder and not only a sample size effect.

B. Within-office AMI (c03_within_office.csv). AMI vs WIPO of the full clustering,
   computed inside each office group (config: office_groups). If clusters carry WIPO
   information only through the office mix, the within-office AMI drops.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_mutual_info_score as ami
from sklearn.metrics import adjusted_rand_score as ari
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    args = parser.parse_args()
    cfg = common.load_config(args.config)
    run = common.run_dir(cfg, args.quick)
    info = common.read_run_info(run)
    seed = cfg["seeds"][0]
    groups = cfg["office_groups"]

    full = {m: p for c, m, p in common.assignment_files(run) if c == "full"}
    nocn = {m: p for c, m, p in common.assignment_files(run) if c == "exclude-cn"}
    removal_rows, office_rows = [], []

    for model, path in full.items():
        a = pd.read_parquet(path)
        a["publication_number"] = a["publication_number"].astype(str)
        b = pd.read_parquet(nocn[model])
        b["publication_number"] = b["publication_number"].astype(str)
        pos_kept = pd.Index(a["publication_number"]).get_indexer(b["publication_number"])
        if (pos_kept < 0).any():
            raise ValueError(f"{model}: exclude-cn patents missing from the full cohort")
        X = common.load_matrix(info["embeddings_dir"], model, a["publication_number"])
        group = a["office"].map(lambda o: common.office_group(o, groups)).to_numpy()
        n_keep = len(b)

        for k in cfg["k"]:
            col = f"cluster_k{k}"
            labels = a[col].to_numpy()

            # B. within-office AMI
            for g in groups + ["Other"]:
                mask = group == g
                if mask.sum() > k:
                    office_rows.append({"model": model, "k": k, "office_group": g, "n": int(mask.sum()),
                                        "AMI_selection": ami(a.loc[mask, "selection_field_primary"], labels[mask])})

            # A. removal test
            scenarios = {"remove-CN": (pos_kept, b[col].to_numpy())}
            for draw in range(cfg["random_removal_draws"]):
                rng = np.random.default_rng(seed * 100 + draw)
                keep = np.sort(rng.choice(len(a), size=n_keep, replace=False))
                with threadpool_limits(limits=cfg["threads"]):
                    refit = KMeans(k, init="k-means++", n_init=cfg["n_init"], max_iter=cfg["max_iter"],
                                   random_state=seed, algorithm="lloyd").fit_predict(X[keep])
                scenarios[f"remove-random-{draw + 1}"] = (keep, refit)
            for name, (keep, refit) in scenarios.items():
                sel = a["selection_field_primary"].to_numpy()[keep]
                before = ami(sel, labels[keep])
                after = ami(sel, refit)
                removal_rows.append({"model": model, "k": k, "scenario": name, "n_kept": len(keep),
                                     "ARI_full_vs_refit": ari(labels[keep], refit),
                                     "AMI_selection_before": before, "AMI_selection_after": after,
                                     "AMI_change": after - before})
            print(f"{model:24s} K={k:2d} " + " ".join(
                f"{r['scenario']}={r['ARI_full_vs_refit']:.2f}" for r in removal_rows[-len(scenarios):]))

    folder = run / "controls"
    folder.mkdir(parents=True, exist_ok=True)
    removal = pd.DataFrame(removal_rows)
    removal.to_csv(folder / "c03_cn_vs_random.csv", index=False)
    pd.DataFrame(office_rows).to_csv(folder / "c03_within_office.csv", index=False)

    removal["kind"] = np.where(removal.scenario == "remove-CN", "remove-CN", "remove-random")
    summary = (removal.groupby(["model", "k", "kind"])[["ARI_full_vs_refit", "AMI_change"]].mean()
               .unstack("kind").round(3))
    summary.columns = [f"{v}_{kind}" for v, kind in summary.columns]
    summary.reset_index().to_csv(folder / "c03_summary.csv", index=False)
    print(summary.to_string())
    print(f"wrote {folder}")


if __name__ == "__main__":
    main()
