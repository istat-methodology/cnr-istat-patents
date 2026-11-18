#!/usr/bin/env python3
"""Full-corpus WIPO32 patent embedding clustering and profiling pipeline.

The script consumes the repository's publication-level Parquet file and
precomputed embedding matrices. It does not generate embeddings or modify input
files. See README.md in this folder for the intended Azure command.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import (
    adjusted_mutual_info_score,
    adjusted_rand_score,
    silhouette_score,
)
from sklearn.preprocessing import normalize
from threadpoolctl import threadpool_limits


DEFAULT_MODELS = [
    "bge-m3",
    "qwen3-embedding-4b",
    "qwen3-embedding-0.6b",
    "embeddinggemma-300m",
    "paecter",
    "pat-specter",
    "sbert-adapt-ub",
    "mpnet",
]

REQUIRED_COLUMNS = {
    "publication_number",
    "office",
    "kind_code",
    "title_clean",
    "abstract_clean",
    "ipc_codes",
    "wipo_field_numbers",
}


def parse_int_list(value: Any) -> list[int]:
    if value is None:
        return []
    if isinstance(value, (float, np.floating)) and math.isnan(float(value)):
        return []
    if isinstance(value, (list, tuple, np.ndarray, pd.Series)):
        items = value
    else:
        items = re.split(r"[;,|]", str(value))
    result: set[int] = set()
    for item in items:
        try:
            result.add(int(item))
        except (TypeError, ValueError):
            continue
    return sorted(result)


def parse_ipc_codes(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    return [
        re.sub(r"\s+", "", token).upper()
        for token in str(value).split(";")
        if re.sub(r"\s+", "", token)
    ]


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_")


def ensure_unique_ids(frame: pd.DataFrame, description: str) -> None:
    ids = frame["publication_number"].astype("string")
    if ids.isna().any() or ids.duplicated().any():
        raise ValueError(f"{description} must have unique, non-missing publication IDs")


def load_corpus(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Corpus is missing required columns: {sorted(missing)}")
    frame["publication_number"] = frame["publication_number"].astype("string")
    frame["office"] = frame["office"].fillna("Unknown").astype(str)
    frame["kind_code"] = frame["kind_code"].fillna("Unknown").astype(str)
    ensure_unique_ids(frame, "Publication-level corpus")
    frame["selection_fields"] = frame["wipo_field_numbers"].map(parse_int_list)
    if frame["selection_fields"].map(len).eq(0).any():
        raise ValueError("Some publications have no WIPO selection field")
    frame["selection_field_primary"] = frame["selection_fields"].map(min)
    frame["ipc_code_list"] = frame["ipc_codes"].map(parse_ipc_codes)
    return frame


def load_wipo_prefixes(path: Path) -> tuple[dict[int, tuple[str, ...]], dict[int, str]]:
    rules = pd.read_excel(path, sheet_name="IPC Tech Concordance", header=6)
    required = {"Field_number", "Field_en", "IPC_code"}
    if not required.issubset(rules.columns):
        raise ValueError(f"WIPO concordance is missing columns: {sorted(required)}")
    rules = rules.loc[pd.to_numeric(rules["Field_number"], errors="coerce") <= 32].copy()
    rules["Field_number"] = rules["Field_number"].astype(int)
    rules["prefix"] = rules["IPC_code"].astype(str).str.upper().str.replace(r"\s+", "", regex=True)
    if not rules["prefix"].str.endswith("%").all():
        raise ValueError("Expected all WIPO IPC rules for fields 1–32 to be prefix rules ending in %")
    prefixes = {
        int(field): tuple(sorted(set(group["prefix"].str[:-1])))
        for field, group in rules.groupby("Field_number")
    }
    names = rules.drop_duplicates("Field_number").set_index("Field_number")["Field_en"].to_dict()
    expected = set(range(1, 33))
    if set(prefixes) != expected:
        raise ValueError(f"Expected WIPO fields 1–32; found {sorted(prefixes)}")
    return prefixes, {int(k): str(v) for k, v in names.items()}


def compatible_fields(codes: list[str], prefixes: dict[int, tuple[str, ...]]) -> list[int]:
    matches: set[int] = set()
    for code in codes:
        for field, starts in prefixes.items():
            if any(code.startswith(prefix) for prefix in starts):
                matches.add(field)
    return sorted(matches)


def build_wipo_matches(
    corpus: pd.DataFrame, prefixes: dict[int, tuple[str, ...]], names: dict[int, str]
) -> pd.DataFrame:
    out = corpus.copy()
    out["ipc_compatible_fields"] = out["ipc_code_list"].map(
        lambda codes: compatible_fields(codes, prefixes)
    )
    failures = out.apply(
        lambda row: not set(row["selection_fields"]).issubset(set(row["ipc_compatible_fields"])),
        axis=1,
    )
    if failures.any():
        ids = out.loc[failures, "publication_number"].head(5).tolist()
        raise ValueError(
            "IPC–WIPO crosswalk did not reproduce the selected field for some patents; "
            f"examples: {ids}"
        )
    out["ipc_compatible_field_names"] = out["ipc_compatible_fields"].map(
        lambda values: [names[value] for value in values]
    )
    if out["ipc_compatible_fields"].map(len).eq(0).any():
        raise ValueError("Some publications do not match any of WIPO fields 1–32")
    out["ipc_compatible_field_primary"] = out["ipc_compatible_fields"].map(min)
    return out


def write_corpus_audit(frame: pd.DataFrame, output: Path, names: dict[int, str]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    n = len(frame)
    ipc_n = frame["ipc_code_list"].map(len)
    compatible_n = frame["ipc_compatible_fields"].map(len)
    metrics = [
        ("n_publications", n),
        ("mean_ipc_codes", float(ipc_n.mean())),
        ("median_ipc_codes", float(ipc_n.median())),
        ("share_with_multiple_ipc_codes", float(ipc_n.ge(2).mean())),
        ("mean_ipc_compatible_wipo_fields", float(compatible_n.mean())),
        ("share_with_multiple_ipc_compatible_wipo_fields", float(compatible_n.ge(2).mean())),
        ("share_office_cn", float(frame["office"].eq("CN").mean())),
        (
            "share_abstract_placeholder",
            float(frame["abstract_is_placeholder"].mean())
            if "abstract_is_placeholder" in frame
            else float("nan"),
        ),
    ]
    pd.DataFrame(metrics, columns=["measure", "value"]).to_csv(
        output / "corpus_overview.csv", index=False
    )
    (frame[["publication_number", "office", "kind_code", "ipc_codes", "selection_fields",
            "ipc_compatible_fields", "ipc_compatible_field_names"]]
     .to_parquet(output / "publication_wipo_matches.parquet", index=False))

    selection_rows = frame[["publication_number", "office", "kind_code", "selection_fields"]].explode(
        "selection_fields"
    ).rename(columns={"selection_fields": "wipo_field_number"})
    selection_rows["wipo_field_number"] = selection_rows["wipo_field_number"].astype(int)
    selection_rows["wipo_field_name"] = selection_rows["wipo_field_number"].map(names)
    selection_rows.groupby(["office", "wipo_field_number", "wipo_field_name"], as_index=False).size().to_csv(
        output / "office_by_selection_field.csv", index=False
    )
    selection_rows.groupby(
        ["office", "kind_code", "wipo_field_number", "wipo_field_name"], as_index=False
    ).size().to_csv(output / "office_kind_code_by_selection_field.csv", index=False)

    compatible_rows = frame[["publication_number", "office", "ipc_compatible_fields"]].explode(
        "ipc_compatible_fields"
    ).rename(columns={"ipc_compatible_fields": "wipo_field_number"})
    compatible_rows["wipo_field_number"] = compatible_rows["wipo_field_number"].astype(int)
    compatible_rows["wipo_field_name"] = compatible_rows["wipo_field_number"].map(names)
    compatible_rows.groupby(["office", "wipo_field_number", "wipo_field_name"], as_index=False).size().to_csv(
        output / "office_by_ipc_compatible_field.csv", index=False
    )
    compatible_n.value_counts().sort_index().rename_axis("n_ipc_compatible_fields").reset_index(
        name="n_publications"
    ).to_csv(output / "ipc_wipo_overlap_distribution.csv", index=False)
    frame.groupby("office", as_index=False).size().sort_values("size", ascending=False).to_csv(
        output / "office_counts.csv", index=False
    )
    print(f"Corpus audit saved: {output}")


def load_embedding(
    embeddings_root: Path, model: str, corpus: pd.DataFrame
) -> tuple[np.ndarray, pd.DataFrame]:
    model_dir = embeddings_root / model
    matrix_path = model_dir / "embeddings.npy"
    ids_path = model_dir / "ids.parquet"
    if not matrix_path.exists() or not ids_path.exists():
        raise FileNotFoundError(f"Expected {matrix_path} and {ids_path}")
    ids = pd.read_parquet(ids_path)
    if "publication_number" not in ids:
        raise ValueError(f"Missing publication_number in {ids_path}")
    ids["publication_number"] = ids["publication_number"].astype("string")
    ensure_unique_ids(ids, f"Embedding IDs for {model}")
    matrix = np.load(matrix_path, mmap_mode="r", allow_pickle=False)
    if matrix.ndim != 2 or matrix.shape[0] != len(ids):
        raise ValueError(f"Unexpected embedding shape for {model}: {matrix.shape}")
    if len(ids) != len(corpus):
        raise ValueError(
            f"{model}: expected {len(corpus)} embedding IDs, found {len(ids)}"
        )
    matrix_positions = pd.Index(ids["publication_number"]).get_indexer(
        corpus["publication_number"]
    )
    if (matrix_positions < 0).any():
        missing_ids = corpus.loc[matrix_positions < 0, "publication_number"].head(5).tolist()
        raise ValueError(f"{model}: corpus IDs absent from embeddings, e.g. {missing_ids}")
    if not np.array_equal(matrix_positions, np.arange(len(corpus))):
        matrix = matrix[matrix_positions]
    return matrix, corpus.reset_index(drop=True)


def ctfidf_terms(texts: pd.Series, labels: np.ndarray, k: int, top_n: int) -> dict[int, list[str]]:
    cluster_docs = []
    for cluster in range(k):
        joined = texts.iloc[np.flatnonzero(labels == cluster)].fillna("").astype(str).str.cat(sep=" ")
        cluster_docs.append(joined)
    vectorizer = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.85,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9-]+\b",
    )
    try:
        counts = vectorizer.fit_transform(cluster_docs).astype(np.float64)
    except ValueError as exc:
        return {cluster: [] for cluster in range(k)}
    totals = np.asarray(counts.sum(axis=1)).ravel()
    term_totals = np.asarray(counts.sum(axis=0)).ravel()
    avg_total = float(totals.mean()) if len(totals) else 0.0
    idf = np.log1p(avg_total / np.maximum(term_totals, 1.0))
    normalized_tf = counts.multiply(1.0 / np.maximum(totals[:, None], 1.0))
    scores = normalized_tf.multiply(idf).toarray()
    terms = np.asarray(vectorizer.get_feature_names_out())
    result: dict[int, list[str]] = {}
    for cluster in range(k):
        order = np.argsort(scores[cluster])[::-1]
        result[cluster] = [str(terms[j]) for j in order[:top_n] if scores[cluster, j] > 0]
    return result


def make_profile(
    meta: pd.DataFrame,
    labels: np.ndarray,
    km: KMeans,
    X: np.ndarray,
    cohort_name: str,
    model: str,
    k: int,
    names: dict[int, str],
    representatives: int,
    boundary_n: int,
    top_terms: int,
    output: Path,
) -> None:
    local = meta.copy()
    local["cluster"] = labels.astype(int)
    local["text_for_terms"] = (
        local["title_clean"].fillna("").astype(str)
        + ". "
        + local["abstract_clean"].fillna("").astype(str)
    )
    term_map = ctfidf_terms(local["text_for_terms"], labels, k, top_terms)
    term_distances = km.transform(X)
    nearest = np.argsort(term_distances, axis=1)
    nearest_gap = term_distances[np.arange(len(X)), nearest[:, 1]] - term_distances[
        np.arange(len(X)), nearest[:, 0]
    ] if k > 1 else np.full(len(X), np.nan)

    profile_rows: list[dict[str, Any]] = []
    office_rows: list[dict[str, Any]] = []
    card_rows: list[dict[str, Any]] = []
    example_rows: list[dict[str, Any]] = []
    cohort_n = len(local)
    office_baseline = local["office"].value_counts(normalize=True).to_dict()

    for field_kind, col in [
        ("ipc_compatible", "ipc_compatible_fields"),
        ("selection_all", "selection_fields"),
    ]:
        baseline: dict[int, float] = {}
        for field in range(1, 33):
            baseline[field] = float(local[col].map(lambda xs: field in xs).mean())
        for cluster in range(k):
            subset = local.loc[local["cluster"] == cluster]
            subset_n = len(subset)
            if subset_n == 0:
                continue
            for field in range(1, 33):
                count = int(subset[col].map(lambda xs: field in xs).sum())
                if count == 0:
                    continue
                share = count / subset_n
                base = baseline[field]
                profile_rows.append(
                    {
                        "cohort": cohort_name,
                        "model": model,
                        "k": k,
                        "cluster": cluster,
                        "wipo_profile_type": field_kind,
                        "wipo_field_number": field,
                        "wipo_field_name": names[field],
                        "n_patents": count,
                        "cluster_share": share,
                        "cohort_share": base,
                        "lift": share / base if base else np.nan,
                    }
                )

    for cluster in range(k):
        members = np.flatnonzero(labels == cluster)
        if not len(members):
            continue
        assigned_dist = term_distances[members, cluster]
        central_order = members[np.argsort(assigned_dist)[:representatives]]
        for rank, idx in enumerate(central_order, start=1):
            row = local.iloc[idx]
            example_rows.append(
                {
                    "cohort": cohort_name,
                    "model": model,
                    "k": k,
                    "cluster": cluster,
                    "example_type": "central",
                    "rank": rank,
                    "center_distance_euclidean": float(term_distances[idx, cluster]),
                    "boundary_margin": float(nearest_gap[idx]),
                    **example_metadata(row),
                }
            )
        best_wipo = sorted(
            [r for r in profile_rows if r["cluster"] == cluster and r["wipo_profile_type"] == "ipc_compatible"],
            key=lambda r: (-r["cluster_share"], r["wipo_field_number"]),
        )[:5]
        selected_wipo = sorted(
            [r for r in profile_rows if r["cluster"] == cluster and r["wipo_profile_type"] == "selection_all"],
            key=lambda r: (-r["cluster_share"], r["wipo_field_number"]),
        )[:5]
        office_counts = local.loc[local["cluster"] == cluster, "office"].value_counts()
        for office, count in office_counts.items():
            share = float(count / len(members))
            baseline = float(office_baseline.get(office, 0.0))
            office_rows.append(
                {
                    "cohort": cohort_name,
                    "model": model,
                    "k": k,
                    "cluster": cluster,
                    "office": office,
                    "n_patents": int(count),
                    "cluster_share": share,
                    "cohort_share": baseline,
                    "lift": share / baseline if baseline else np.nan,
                }
            )
        top_offices = sorted(
            office_counts.items(), key=lambda item: (-int(item[1]), str(item[0]))
        )[:5]
        card_rows.append(
            {
                "cohort": cohort_name,
                "model": model,
                "k": k,
                "cluster": cluster,
                "n_patents": len(members),
                "cluster_share_of_cohort": len(members) / cohort_n,
                "ctfidf_terms": " | ".join(term_map.get(cluster, [])),
                "top_ipc_compatible_wipo": " | ".join(
                    f"{r['wipo_field_number']:02d} {r['wipo_field_name']} ({r['cluster_share']:.1%}; lift {r['lift']:.2f})"
                    for r in best_wipo
                ),
                "top_selection_wipo": " | ".join(
                    f"{r['wipo_field_number']:02d} {r['wipo_field_name']} ({r['cluster_share']:.1%})"
                    for r in selected_wipo
                ),
                "top_offices": " | ".join(
                    f"{office} ({count / len(members):.1%})" for office, count in top_offices
                ),
            }
        )

    # Boundary examples have the smallest gap between their closest two centers.
    for rank, idx in enumerate(np.argsort(nearest_gap)[:boundary_n], start=1):
        row = local.iloc[idx]
        assigned = int(labels[idx])
        alternative = int(nearest[idx, 1]) if k > 1 else -1
        example_rows.append(
            {
                "cohort": cohort_name,
                "model": model,
                "k": k,
                "cluster": assigned,
                "example_type": "boundary",
                "rank": rank,
                "center_distance_euclidean": float(term_distances[idx, assigned]),
                "boundary_margin": float(nearest_gap[idx]),
                "nearest_alternative_cluster": alternative,
                **example_metadata(row),
            }
        )

    stem = f"{slug(cohort_name)}__{slug(model)}__k{k}"
    pd.DataFrame(profile_rows).to_csv(output / f"{stem}__wipo_profiles.csv", index=False)
    pd.DataFrame(office_rows).to_csv(output / f"{stem}__office_profiles.csv", index=False)
    pd.DataFrame(card_rows).to_csv(output / f"{stem}__cluster_cards.csv", index=False)
    pd.DataFrame(example_rows).to_csv(output / f"{stem}__patent_examples.csv", index=False)


def example_metadata(row: pd.Series) -> dict[str, Any]:
    return {
        "publication_number": str(row["publication_number"]),
        "office": str(row["office"]),
        "kind_code": str(row["kind_code"]),
        "selection_fields": ";".join(map(str, row["selection_fields"])),
        "ipc_compatible_fields": ";".join(map(str, row["ipc_compatible_fields"])),
        "title": str(row.get("title_clean", "")),
        "abstract": str(row.get("abstract_clean", "")),
    }


def run(args: argparse.Namespace) -> Path:
    output_root = args.output_dir.expanduser().resolve()
    run_name = args.run_name or datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    output = output_root / run_name
    output.mkdir(parents=True, exist_ok=False)
    for sub in ["audit", "metrics", "assignments", "profiles"]:
        (output / sub).mkdir()

    print(f"Loading publication data: {args.data}")
    corpus = load_corpus(args.data.expanduser().resolve())
    prefixes, field_names = load_wipo_prefixes(args.concordance.expanduser().resolve())
    corpus = build_wipo_matches(corpus, prefixes, field_names)
    write_corpus_audit(corpus, output / "audit", field_names)

    requested_cohorts = args.cohorts
    cohort_masks = {
        "full": np.ones(len(corpus), dtype=bool),
        "exclude-cn": corpus["office"].ne("CN").to_numpy(),
    }
    unknown = set(requested_cohorts).difference(cohort_masks)
    if unknown:
        raise ValueError(f"Unknown cohorts: {sorted(unknown)}")

    all_metrics: list[dict[str, Any]] = []
    all_stability: list[dict[str, Any]] = []
    reference_labels: dict[tuple[str, int, str], np.ndarray] = {}
    reference_ids: dict[tuple[str, str], np.ndarray] = {}
    config = {
        "data": str(args.data.expanduser().resolve()),
        "embeddings_dir": str(args.embeddings_dir.expanduser().resolve()),
        "models": args.models,
        "cohorts": requested_cohorts,
        "k_values": args.k,
        "seeds": args.seeds,
        "reference_seed": args.seeds[0],
        "n_init": args.n_init,
        "max_iter": args.max_iter,
        "threads": args.threads,
        "silhouette_sample": args.silhouette_sample,
        "ctfidf_top_terms": args.top_terms,
        "wipo_mapping": "WIPO IPC Tech Concordance, fields 1-32, prefix matching as in Notebook 05",
        "wipo_primary_ami": "Notebook 09 convention = lowest IPC-compatible WIPO field number; selection-field AMI is also reported separately; all compatible/selection fields are separately profiled",
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "run_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    for model in args.models:
        print(f"\nLoading embedding model: {model}")
        matrix, aligned_meta = load_embedding(
            args.embeddings_dir.expanduser().resolve(), model, corpus
        )
        print(f"  shape={matrix.shape}, dtype={matrix.dtype}")
        for cohort_name in requested_cohorts:
            positions = np.flatnonzero(cohort_masks[cohort_name])
            meta = aligned_meta.iloc[positions].reset_index(drop=True)
            # The source matrices are float16 and L2-normalized. Renormalize after
            # conversion to float32 to remove storage-rounding error.
            X = np.asarray(matrix[positions], dtype=np.float32)
            if not np.isfinite(X).all():
                raise ValueError(f"{model}/{cohort_name}: embeddings contain NaN or infinity")
            norms = np.linalg.norm(X, axis=1)
            if np.any(norms == 0):
                raise ValueError(f"{model}/{cohort_name}: zero-vector embeddings found")
            X = normalize(X, norm="l2", copy=False)
            n = len(meta)
            if n < max(args.k) + 2:
                raise ValueError(f"Cohort {cohort_name} is too small for requested K")
            rng = np.random.default_rng(args.silhouette_seed)
            sample_idx = np.sort(
                rng.choice(n, size=min(args.silhouette_sample, n), replace=False)
            )
            seed_labels_by_k: dict[int, dict[int, np.ndarray]] = {}
            reference_models: dict[int, KMeans] = {}
            reference_labels_by_k: dict[int, np.ndarray] = {}

            for k in args.k:
                seed_labels_by_k[k] = {}
                for seed in args.seeds:
                    started = time.perf_counter()
                    km = KMeans(
                        n_clusters=k,
                        init="k-means++",
                        n_init=args.n_init,
                        max_iter=args.max_iter,
                        random_state=seed,
                        algorithm="lloyd",
                    )
                    with threadpool_limits(limits=args.threads):
                        labels = km.fit_predict(X).astype(np.int32, copy=False)
                    elapsed = time.perf_counter() - started
                    seed_labels_by_k[k][seed] = labels
                    if seed == args.seeds[0]:
                        reference_models[k] = km
                        reference_labels_by_k[k] = labels
                        reference_labels[(cohort_name, k, model)] = labels.copy()
                        reference_ids[(cohort_name, model)] = meta[
                            "publication_number"
                        ].astype(str).to_numpy()

                    sampled_labels = labels[sample_idx]
                    if len(np.unique(sampled_labels)) > 1 and len(np.unique(sampled_labels)) < len(sampled_labels):
                        sil = float(
                            silhouette_score(
                                X[sample_idx], sampled_labels, metric="cosine"
                            )
                        )
                    else:
                        sil = float("nan")
                    counts = np.bincount(labels, minlength=k)
                    score = {
                        "cohort": cohort_name,
                        "model": model,
                        "k": k,
                        "seed": seed,
                        "n_patents": n,
                        "silhouette_cosine_sample": sil,
                        "silhouette_sample_n": len(sample_idx),
                        "AMI_WIPO_selection_primary": float(
                            adjusted_mutual_info_score(meta["selection_field_primary"], labels)
                        ),
                        "AMI_WIPO_compatible_primary": float(
                            adjusted_mutual_info_score(meta["ipc_compatible_field_primary"], labels)
                        ),
                        "AMI_office": float(adjusted_mutual_info_score(meta["office"], labels)),
                        "largest_cluster_share": float(counts.max() / n),
                        "smallest_cluster_n": int(counts.min()),
                        "largest_cluster_n": int(counts.max()),
                        "fit_seconds": elapsed,
                    }
                    all_metrics.append(score)
                    print(
                        f"  {cohort_name:9s} K={k:2d} seed={seed}: "
                        f"sil={sil:.4f} AMI_WIPO={score['AMI_WIPO_selection_primary']:.4f} "
                        f"fit={elapsed / 60:.1f} min"
                    )

                for seed_a, seed_b in itertools.combinations(args.seeds, 2):
                    all_stability.append(
                        {
                            "cohort": cohort_name,
                            "model": model,
                            "k": k,
                            "seed_a": seed_a,
                            "seed_b": seed_b,
                            "ARI": float(
                                adjusted_rand_score(
                                    seed_labels_by_k[k][seed_a], seed_labels_by_k[k][seed_b]
                                )
                            ),
                        }
                    )

            assignment = meta[
                [
                    "publication_number",
                    "office",
                    "kind_code",
                    "publication_year",
                    "selection_fields",
                    "selection_field_primary",
                    "ipc_compatible_field_primary",
                    "ipc_compatible_fields",
                    "ipc_compatible_field_names",
                    "abstract_is_placeholder",
                ]
            ].copy()
            for k, labels in reference_labels_by_k.items():
                assignment[f"cluster_k{k}"] = labels
            assignment.to_parquet(
                output / "assignments" / f"{slug(cohort_name)}__{slug(model)}.parquet",
                index=False,
            )
            for k in args.k:
                make_profile(
                    meta=meta,
                    labels=reference_labels_by_k[k],
                    km=reference_models[k],
                    X=X,
                    cohort_name=cohort_name,
                    model=model,
                    k=k,
                    names=field_names,
                    representatives=args.representatives,
                    boundary_n=args.boundary_examples,
                    top_terms=args.top_terms,
                    output=output / "profiles",
                )
            # Checkpoint after each completed cohort so interruption during a
            # later model/cohort leaves usable metrics for finished work.
            pd.DataFrame(all_metrics).to_csv(
                output / "metrics" / "seed_metrics_progress.csv", index=False
            )
            pd.DataFrame(all_stability).to_csv(
                output / "metrics" / "seed_stability_progress.csv", index=False
            )
            del X
        del matrix

    metrics = pd.DataFrame(all_metrics)
    metrics.to_csv(output / "metrics" / "seed_metrics.csv", index=False)
    stability = pd.DataFrame(all_stability)
    stability.to_csv(output / "metrics" / "seed_stability_ari.csv", index=False)
    if not metrics.empty:
        summary = (
            metrics.groupby(["cohort", "model", "k"], as_index=False)
            .agg(
                n_seeds=("seed", "nunique"),
                n_patents=("n_patents", "first"),
                silhouette_mean=("silhouette_cosine_sample", "mean"),
                silhouette_sd=("silhouette_cosine_sample", "std"),
                AMI_WIPO_selection_primary_mean=("AMI_WIPO_selection_primary", "mean"),
                AMI_WIPO_compatible_primary_mean=("AMI_WIPO_compatible_primary", "mean"),
                AMI_office_mean=("AMI_office", "mean"),
                largest_cluster_share_mean=("largest_cluster_share", "mean"),
                fit_seconds_mean=("fit_seconds", "mean"),
            )
        )
        if not stability.empty:
            stab_summary = stability.groupby(["cohort", "model", "k"], as_index=False).agg(
                seed_ARI_mean=("ARI", "mean"), seed_ARI_min=("ARI", "min")
            )
            summary = summary.merge(stab_summary, on=["cohort", "model", "k"], how="left")
        summary.to_csv(output / "metrics" / "model_k_summary.csv", index=False)

    cross_rows = []
    for cohort_name in requested_cohorts:
        for k in args.k:
            for model_a, model_b in itertools.combinations(args.models, 2):
                key_a = (cohort_name, k, model_a)
                key_b = (cohort_name, k, model_b)
                if key_a in reference_labels and key_b in reference_labels:
                    cross_rows.append(
                        {
                            "cohort": cohort_name,
                            "k": k,
                            "seed": args.seeds[0],
                            "model_a": model_a,
                            "model_b": model_b,
                            "ARI": float(
                                adjusted_rand_score(reference_labels[key_a], reference_labels[key_b])
                            ),
                        }
                    )
    pd.DataFrame(cross_rows).to_csv(
        output / "metrics" / "cross_model_ari_reference_seed.csv", index=False
    )

    cohort_rows = []
    if "full" in requested_cohorts and "exclude-cn" in requested_cohorts:
        for model in args.models:
            for k in args.k:
                full_key = ("full", k, model)
                no_cn_key = ("exclude-cn", k, model)
                if full_key not in reference_labels or no_cn_key not in reference_labels:
                    continue
                full_ids = reference_ids[("full", model)]
                no_cn_ids = reference_ids[("exclude-cn", model)]
                full_positions = pd.Index(full_ids).get_indexer(no_cn_ids)
                if (full_positions < 0).any():
                    raise ValueError(f"Could not align full/no-CN IDs for {model}, K={k}")
                cohort_rows.append(
                    {
                        "model": model,
                        "k": k,
                        "seed": args.seeds[0],
                        "n_common_patents": len(no_cn_ids),
                        "ARI_full_fit_vs_no_cn_refit": float(
                            adjusted_rand_score(
                                reference_labels[full_key][full_positions],
                                reference_labels[no_cn_key],
                            )
                        ),
                    }
                )
    pd.DataFrame(cohort_rows).to_csv(
        output / "metrics" / "full_vs_no_cn_refit_ari.csv", index=False
    )

    print(f"\nAnalysis complete. Results: {output}")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="Publication-level Parquet file")
    parser.add_argument("--concordance", type=Path, required=True, help="ipc/ipc_technology.xlsx")
    parser.add_argument("--embeddings-dir", type=Path, required=True, help="Root containing MODEL/embeddings.npy and ids.parquet")
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/results"))
    parser.add_argument("--run-name", help="Optional output directory name; must not already exist")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--cohorts", nargs="+", choices=["full", "exclude-cn"], default=["full", "exclude-cn"])
    parser.add_argument("--k", nargs="+", type=int, default=[8, 16])
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--n-init", type=int, default=10)
    parser.add_argument("--max-iter", type=int, default=300)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--silhouette-sample", type=int, default=1200)
    parser.add_argument("--silhouette-seed", type=int, default=42)
    parser.add_argument("--representatives", type=int, default=5)
    parser.add_argument("--boundary-examples", type=int, default=5)
    parser.add_argument("--top-terms", type=int, default=10)
    return parser


if __name__ == "__main__":
    try:
        run(build_parser().parse_args())
    except KeyboardInterrupt:
        print("Interrupted. Outputs already written remain available; rerun with a new --run-name.", file=sys.stderr)
        raise SystemExit(130)
