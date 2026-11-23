#!/usr/bin/env python3
"""Control 1 - reference scale for AMI against the WIPO field.

AMI with the 32 WIPO fields cannot reach 1 with K=8 or 16 clusters, and a
patent-aware method is not expected to reproduce WIPO anyway. So an AMI value
means little alone. This control puts the models on a scale with these partitions
of the same patents:

  random          random labels, K groups          -> floor (about 0)
  sector-oracle   the 4 WIPO sectors, no clustering -> what 4 coarse groups reach
  merge-oracle    WIPO fields merged into K groups, smallest first
                  (best coarsening of WIPO into K groups, so the practical ceiling)
  ipc-kmeans      K-means on IPC subclasses only (no text)
  <model>         the K-means of each model (reference seed, from step 2)

Output: controls/c01_reference_scale.csv (one row per cohort, K, partition).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_mutual_info_score as ami
from sklearn.preprocessing import normalize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def merge_oracle(fields: pd.Series, k: int) -> np.ndarray:
    """Merge the smallest WIPO groups until K remain: a coarsening of WIPO with K groups."""
    groups = {f: [f] for f in fields.unique()}
    sizes = fields.value_counts().to_dict()
    size = {f: sizes[f] for f in groups}
    while len(groups) > k:
        a, b = sorted(groups, key=lambda g: size[g])[:2]
        groups[a] += groups.pop(b)
        size[a] += size.pop(b)
    lookup = {f: g for g, members in groups.items() for f in members}
    return fields.map(lookup).to_numpy()


def ipc_kmeans(ipc_lists: pd.Series, k: int, seed: int, n_init: int, threads: int) -> np.ndarray:
    docs = [" ".join(codes) for codes in ipc_lists]
    tfidf = TfidfVectorizer(token_pattern=r"\S+", lowercase=False, sublinear_tf=True).fit_transform(docs)
    dims = min(64, tfidf.shape[1] - 1)
    X = TruncatedSVD(dims, random_state=seed).fit_transform(tfidf)
    X = normalize(X)
    from threadpoolctl import threadpool_limits

    with threadpool_limits(limits=threads):
        return KMeans(k, init="k-means++", n_init=n_init, random_state=seed).fit_predict(X)


def scores(frame: pd.DataFrame, labels) -> dict:
    return {
        "AMI_selection": ami(frame["selection_field_primary"], labels),
        "AMI_compatible_primary": ami(frame["ipc_compatible_field_primary"], labels),
        "AMI_office": ami(frame["office"], labels),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    args = parser.parse_args()
    cfg = common.load_config(args.config)
    run = common.run_dir(cfg, args.quick)
    info = common.read_run_info(run)
    seed = cfg["seeds"][0]

    corpus = pd.read_parquet(info["data"], columns=["publication_number", "ipc_subclasses"])
    corpus["publication_number"] = corpus["publication_number"].astype(str)
    ipc_by_id = corpus.set_index("publication_number")["ipc_subclasses"]

    rows = []
    for cohort in cfg["cohorts"]:
        files = {m: p for c, m, p in common.assignment_files(run) if c == cohort}
        first = pd.read_parquet(next(iter(files.values())))
        first["publication_number"] = first["publication_number"].astype(str)
        ipc = ipc_by_id.loc[first["publication_number"]].reset_index(drop=True)
        sector = first["selection_field_primary"].map(common.sector_of)
        rng = np.random.default_rng(seed)
        for k in cfg["k"]:
            partitions = {
                "random": ("reference", rng.integers(0, k, len(first))),
                "sector-oracle": ("reference", sector.astype("category").cat.codes.to_numpy()),
                "merge-oracle": ("reference", merge_oracle(first["selection_field_primary"], k)),
                "ipc-kmeans": ("reference", ipc_kmeans(ipc, k, seed, cfg["n_init"], cfg["threads"])),
            }
            for model, path in files.items():
                a = pd.read_parquet(path)
                if not a["publication_number"].astype(str).equals(first["publication_number"]):
                    raise ValueError(f"{model}: assignment order differs from the others")
                partitions[model] = (common.kind_of(model), a[f"cluster_k{k}"].to_numpy())
            for name, (kind, labels) in partitions.items():
                n_groups = len(np.unique(labels))
                rows.append({"cohort": cohort, "k": k, "partition": name, "kind": kind,
                             "n_groups": n_groups, **scores(first, labels)})
                print(f"{cohort:10s} K={k:2d} {name:24s} AMI_sel={rows[-1]['AMI_selection']:.3f}")
    out = pd.DataFrame(rows)
    ceiling = out[out.partition == "merge-oracle"].set_index(["cohort", "k"])["AMI_selection"]
    out["share_of_merge_oracle"] = [r.AMI_selection / ceiling[(r.cohort, r.k)] for r in out.itertuples()]
    folder = run / "controls"
    folder.mkdir(parents=True, exist_ok=True)
    out.to_csv(folder / "c01_reference_scale.csv", index=False)
    print(f"wrote {folder / 'c01_reference_scale.csv'}")


if __name__ == "__main__":
    main()
