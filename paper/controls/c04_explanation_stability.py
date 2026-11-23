#!/usr/bin/env python3
"""Control 4 - are the cluster explanations (c-TF-IDF terms) stable?

A cluster card is the list of its top c-TF-IDF terms. A card is trustworthy only if
the same cluster, found again, gets nearly the same terms. For the deep-dive models:

  seed     reference seed vs another seed of K-means (same model, full corpus)
  cohort   full corpus vs exclude-CN refit (same model, patents in common)
  model    reference seed of one model vs another model (full corpus)

Clusters of the two clusterings are matched one to one by the largest overlap of
patents (Hungarian algorithm). For every matched pair we report
  overlap_share   patents in both clusters / patents in the first cluster
  jaccard_terms   Jaccard index of the two top-term sets
and, as a floor, the mean Jaccard of the NOT matched pairs (null_jaccard).

Output: controls/c04_explanation_pairs.csv (matched pairs),
        controls/c04_explanation_summary.csv (one row per comparison).
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def jaccard(a: list[str], b: list[str]) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else float("nan")


def compare(labels_a, labels_b, ids_a, ids_b, texts_by_id, k, top_n):
    """Match clusters on the patents in common; return one row per matched pair + the null."""
    common_ids = pd.Index(ids_a).intersection(pd.Index(ids_b))
    pa = pd.Index(ids_a).get_indexer(common_ids)
    pb = pd.Index(ids_b).get_indexer(common_ids)
    table = np.zeros((k, k), dtype=np.int64)
    np.add.at(table, (labels_a[pa], labels_b[pb]), 1)
    rows, cols = linear_sum_assignment(-table)
    terms_a = common.engine.ctfidf_terms(texts_by_id.loc[ids_a], labels_a, k, top_n)
    terms_b = common.engine.ctfidf_terms(texts_by_id.loc[ids_b], labels_b, k, top_n)
    sizes_a = table.sum(axis=1)
    matched = [{"cluster_a": int(i), "cluster_b": int(j),
                "overlap_share": table[i, j] / max(sizes_a[i], 1),
                "jaccard_terms": jaccard(terms_a[i], terms_b[j])} for i, j in zip(rows, cols)]
    pairs = set(zip(rows, cols))
    null = [jaccard(terms_a[i], terms_b[j]) for i in range(k) for j in range(k) if (i, j) not in pairs]
    return matched, float(np.nanmean(null))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    args = parser.parse_args()
    cfg = common.load_config(args.config)
    run = common.run_dir(cfg, args.quick)
    info = common.read_run_info(run)
    top_n = cfg["explain_top_terms"]

    corpus = pd.read_parquet(info["data"], columns=["publication_number", "title_clean", "abstract_clean"])
    corpus["publication_number"] = corpus["publication_number"].astype(str)
    texts = (corpus["title_clean"].fillna("").astype(str) + ". " + corpus["abstract_clean"].fillna("").astype(str))
    texts.index = corpus["publication_number"]

    full = {m: p for c, m, p in common.assignment_files(run) if c == "full"}
    nocn = {m: p for c, m, p in common.assignment_files(run) if c == "exclude-cn"}
    models = [m for m in cfg["deep_dive_models"] if m in full]
    pair_rows, summary_rows = [], []

    def record(kind, model_a, model_b, k, detail, matched, null):
        for row in matched:
            pair_rows.append({"comparison": kind, "model_a": model_a, "model_b": model_b, "k": k,
                              "detail": detail, **row})
        summary_rows.append({"comparison": kind, "model_a": model_a, "model_b": model_b, "k": k, "detail": detail,
                             "mean_overlap_share": np.mean([r["overlap_share"] for r in matched]),
                             "mean_jaccard_matched": np.nanmean([r["jaccard_terms"] for r in matched]),
                             "min_jaccard_matched": np.nanmin([r["jaccard_terms"] for r in matched]),
                             "mean_jaccard_unmatched": null})

    for k in cfg["explain_k"]:
        col = f"cluster_k{k}"
        ref = {}
        for model in models:
            a = pd.read_parquet(full[model])
            a["publication_number"] = a["publication_number"].astype(str)
            ref[model] = (a["publication_number"].to_numpy(), a[col].to_numpy())
            ids, labels = ref[model]

            # seed: refit with the other seeds
            X = common.load_matrix(info["embeddings_dir"], model, ids)
            for seed in cfg["seeds"][1:]:
                with threadpool_limits(limits=cfg["threads"]):
                    other = KMeans(k, init="k-means++", n_init=cfg["n_init"], max_iter=cfg["max_iter"],
                                   random_state=seed, algorithm="lloyd").fit_predict(X)
                matched, null = compare(labels, other, ids, ids, texts, k, top_n)
                record("seed", model, model, k, f"seed {cfg['seeds'][0]} vs {seed}", matched, null)

            # cohort: full vs exclude-CN
            b = pd.read_parquet(nocn[model])
            ids_b = b["publication_number"].astype(str).to_numpy()
            matched, null = compare(labels, b[col].to_numpy(), ids, ids_b, texts, k, top_n)
            record("cohort", model, model, k, "full vs exclude-cn", matched, null)

        # model vs model
        for m1, m2 in itertools.combinations(models, 2):
            matched, null = compare(ref[m1][1], ref[m2][1], ref[m1][0], ref[m2][0], texts, k, top_n)
            record("model", m1, m2, k, "reference seeds", matched, null)

    folder = run / "controls"
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(pair_rows).to_csv(folder / "c04_explanation_pairs.csv", index=False)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(folder / "c04_explanation_summary.csv", index=False)
    print(summary.round(3).to_string(index=False))
    print(f"wrote {folder}")


if __name__ == "__main__":
    main()
