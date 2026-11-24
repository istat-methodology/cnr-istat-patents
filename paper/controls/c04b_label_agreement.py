#!/usr/bin/env python3
"""Control 4b - do two cluster cards say the same thing, beyond the exact top-10 terms?

Complements the term Jaccard of control 4, which counts a term as shared only when the strings are equal.
For each matched pair of clusters (same matching as control 4: Hungarian algorithm on the patents in common)
it reports, from the cluster cards:

  term_jaccard    Jaccard of the top c-TF-IDF terms, as in control 4
  word_jaccard    Jaccard of the words in those terms (lowercase, plural endings removed)
  top1_same       the most compatible WIPO field is the same
  sector_same     the most compatible WIPO field is in the same WIPO sector
  wipo_cosine     cosine of the WIPO shares listed on the two cards (top fields only)

and, as a floor, the same measures averaged over the NOT matched pairs.
Comparisons: cohort (full vs exclude-CN, same model) and model (full corpus, two models).

A matched pair is the same cluster only if the two clusters share most of their patents. The Hungarian
algorithm always matches every cluster, so pairs with a small overlap are leftovers. The summary therefore
gives the measures for all matched pairs and for the pairs with overlap_share >= MIN_OVERLAP (0.5).
The threshold was chosen after looking at the results of the earlier run; it is a reading aid, not a test.

The WIPO measures are not independent of the clustering target: the field mix of a cluster is a coarse
label of what the cluster contains. They show that the two clusters hold the same kind of patents, not that
the two sets of terms describe them equally well.

Output: controls/c04b_label_pairs.csv (matched pairs), controls/c04b_label_summary.csv (one row per comparison).
Reads <run>/assignments and <run>/profiles (cluster cards). Run after step 2 (cluster).
"""
from __future__ import annotations

import argparse
import itertools
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

SECTORS = [(range(1, 9), "Electrical engineering"), (range(9, 14), "Instruments"),
           (range(14, 25), "Chemistry"), (range(25, 33), "Mechanical engineering")]


def sector(field: int) -> str:
    return next(name for r, name in SECTORS if field in r)


def stem(word: str) -> str:
    w = word.lower()
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def words(terms: list[str]) -> set[str]:
    return {stem(w) for t in terms for w in re.findall(r"[A-Za-z0-9]+", t)}


def jac(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else float("nan")


def parse_wipo(cell: str) -> dict[int, float]:
    out = {}
    for item in str(cell).split("|"):
        m = re.match(r"\s*(\d+)\s+.*?\((\d+(?:\.\d+)?)%", item)
        if m:
            out[int(m.group(1))] = float(m.group(2))
    return out


def cosine(a: dict, b: dict) -> float:
    keys = sorted(set(a) | set(b))
    va, vb = np.array([a.get(k, 0.0) for k in keys]), np.array([b.get(k, 0.0) for k in keys])
    d = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(va @ vb / d) if d else float("nan")


def card_info(cards: pd.DataFrame) -> dict[int, dict]:
    info = {}
    for _, r in cards.iterrows():
        w = parse_wipo(r["top_ipc_compatible_wipo"])
        top = max(w, key=w.get)
        info[int(r["cluster"])] = {"terms": [t.strip() for t in str(r["ctfidf_terms"]).split("|")],
                                   "wipo": w, "top": top, "sector": sector(top)}
    return info


def pair_measures(a: dict, b: dict) -> dict:
    return {"term_jaccard": jac(set(a["terms"]), set(b["terms"])),
            "word_jaccard": jac(words(a["terms"]), words(b["terms"])),
            "top1_same": float(a["top"] == b["top"]),
            "sector_same": float(a["sector"] == b["sector"]),
            "wipo_cosine": cosine(a["wipo"], b["wipo"])}


MIN_OVERLAP = 0.5
MEASURES = ["term_jaccard", "word_jaccard", "top1_same", "sector_same", "wipo_cosine"]


def compare(ass_a, ass_b, cards_a, cards_b, col, k):
    a = ass_a.set_index("publication_number")[col]
    b = ass_b.set_index("publication_number")[col]
    ids = a.index.intersection(b.index)
    table = np.zeros((k, k), dtype=np.int64)
    np.add.at(table, (a.loc[ids].to_numpy(), b.loc[ids].to_numpy()), 1)
    rows, cols = linear_sum_assignment(-table)
    sizes = table.sum(axis=1)
    ia, ib = card_info(cards_a), card_info(cards_b)
    matched = [{"cluster_a": int(i), "cluster_b": int(j), "overlap_share": table[i, j] / max(sizes[i], 1),
                **pair_measures(ia[i], ib[j]),
                "terms_a": " | ".join(ia[i]["terms"][:6]), "terms_b": " | ".join(ib[j]["terms"][:6]),
                "wipo_top_a": ia[i]["top"], "wipo_top_b": ib[j]["top"]} for i, j in zip(rows, cols)]
    mp = set(zip(rows, cols))
    null = pd.DataFrame([pair_measures(ia[i], ib[j]) for i in range(k) for j in range(k) if (i, j) not in mp])
    return matched, null.mean()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, help="paper/config.yaml (default)")
    ap.add_argument("--quick", action="store_true", help="read the -quick run folder")
    ap.add_argument("--run-dir", type=Path, help="override: folder with assignments/ and profiles/ (for tests)")
    ap.add_argument("--models", nargs="+", help="with --run-dir: models to compare")
    ap.add_argument("--k", type=int, default=8, help="with --run-dir: K of the cards")
    args = ap.parse_args()

    if args.run_dir:
        run, models, ks = args.run_dir, args.models, [args.k]
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import common
        cfg = common.load_config(args.config)
        run = common.run_dir(cfg, args.quick)
        models, ks = cfg["deep_dive_models"], list(cfg["explain_k"])
    args.assignments, args.profiles, args.out = run / "assignments", run / "profiles", run / "controls"
    args.models = models

    def load(cohort, model):
        a = pd.read_parquet(args.assignments / f"{cohort}__{model}.parquet")
        a["publication_number"] = a["publication_number"].astype(str)
        c = pd.read_csv(args.profiles / f"{cohort}__{model}__k{args.k}__cluster_cards.csv")
        return a, c

    pairs, summary = [], []

    def record(kind, m1, m2, detail, matched, null):
        for r in matched:
            pairs.append({"comparison": kind, "model_a": m1, "model_b": m2, "k": args.k, "detail": detail, **r})
        row = {"comparison": kind, "model_a": m1, "model_b": m2, "k": args.k, "detail": detail,
               "mean_overlap_share": np.mean([r["overlap_share"] for r in matched])}
        for m in MEASURES:
            row[f"{m}_matched"] = np.nanmean([r[m] for r in matched])
            row[f"{m}_unmatched"] = null[m]
        row["min_word_jaccard_matched"] = np.nanmin([r["word_jaccard"] for r in matched])
        same = [r for r in matched if r["overlap_share"] >= MIN_OVERLAP]
        row["n_pairs"] = len(matched)
        row["n_pairs_overlap"] = len(same)
        for m in MEASURES:
            row[f"{m}_overlap"] = np.nanmean([r[m] for r in same]) if same else float("nan")
        summary.append(row)

    for k in ks:
        args.k = k
        col = f"cluster_k{k}"
        for m in args.models:
            a, ca = load("full", m)
            b, cb = load("exclude-cn", m)
            record("cohort", m, m, "full vs exclude-cn", *compare(a, b, ca, cb, col, k))
        for m1, m2 in itertools.combinations(args.models, 2):
            a, ca = load("full", m1)
            b, cb = load("full", m2)
            record("model", m1, m2, "full corpus", *compare(a, b, ca, cb, col, k))

    args.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(pairs).to_csv(args.out / "c04b_label_pairs.csv", index=False)
    s = pd.DataFrame(summary)
    s.to_csv(args.out / "c04b_label_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(s.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
