#!/usr/bin/env python3
"""Lexical baseline: TF-IDF + truncated SVD (LSA) vectors for the WIPO32 patent corpus.

The output has the same layout as the embedding models, so analysis/run_analysis.py
runs on it without changes:

    <out-dir>/<name>/embeddings.npy   float16, one row per publication, L2-normalised
    <out-dir>/<name>/ids.parquet      publication_number, abstract_is_placeholder
    <out-dir>/<name>/meta.json        parameters and library versions

Text: title followed by abstract (title_clean + " " + abstract_clean), the same rule
as src/generate_embeddings.py.

The vectorizer and the SVD are fitted once on the full corpus (63,968 publications).
The exclude-CN cohort is then clustered from the same vectors, as for the embedding
models. Fitting the vocabulary on the cohort alone would need a separate run.

Usage, from the repository root:

    python src/generate_tfidf_baseline.py
    python analysis/run_analysis.py \\
        --data data/processed/patents_2021-2026_by_publication.parquet \\
        --concordance ipc/ipc_technology.xlsx \\
        --embeddings-dir embeddings \\
        --output-dir ../patent-analysis-results \\
        --models tfidf-svd256
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

REQUIRED = ["publication_number", "title_clean", "abstract_clean"]


def build_texts(df: pd.DataFrame) -> list[str]:
    title = df["title_clean"].fillna("").astype(str).str.strip()
    abstract = df["abstract_clean"].fillna("").astype(str).str.strip()
    return (title + " " + abstract).str.strip().tolist()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=Path("data/processed/patents_2021-2026_by_publication.parquet"))
    parser.add_argument("--out-dir", type=Path, default=Path("embeddings"))
    parser.add_argument("--name", default=None, help="Output folder name (default: tfidf-svd<dims>)")
    parser.add_argument("--dims", type=int, default=256, help="SVD components")
    parser.add_argument("--min-df", type=int, default=5, help="Drop terms in fewer documents")
    parser.add_argument("--max-df", type=float, default=0.5, help="Drop terms in more than this share of documents")
    parser.add_argument("--ngram-max", type=int, default=2, choices=[1, 2], help="1 = unigrams, 2 = unigrams and bigrams")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    name = args.name or f"tfidf-svd{args.dims}"
    out = args.out_dir / name
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.input)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{args.input} is missing columns: {missing}")
    if df["publication_number"].duplicated().any():
        raise ValueError("publication_number must be unique in the by-publication file")
    if "abstract_is_placeholder" not in df.columns:
        df["abstract_is_placeholder"] = False

    texts = build_texts(df)
    print(f"[{name}] {len(texts):,} texts")

    t0 = time.time()
    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        stop_words="english",
        ngram_range=(1, args.ngram_max),
        min_df=args.min_df,
        max_df=args.max_df,
        sublinear_tf=True,
        dtype=np.float32,
    )
    tfidf = vectorizer.fit_transform(texts)
    vocab = tfidf.shape[1]
    print(f"[{name}] TF-IDF matrix {tfidf.shape}, {tfidf.nnz:,} non-zero values")

    empty_rows = int((tfidf.getnnz(axis=1) == 0).sum())
    if empty_rows:
        raise RuntimeError(
            f"{empty_rows} publications have no term left after filtering; "
            "lower --min-df or raise --max-df"
        )

    svd = TruncatedSVD(n_components=args.dims, algorithm="randomized", n_iter=7, random_state=args.seed)
    reduced = svd.fit_transform(tfidf)
    reduced = normalize(reduced.astype(np.float32), norm="l2")
    if not np.isfinite(reduced).all() or (np.linalg.norm(reduced, axis=1) == 0).any():
        raise RuntimeError("Non-finite or zero vectors after SVD")
    explained = float(svd.explained_variance_ratio_.sum())
    print(f"[{name}] SVD {args.dims} dims, explained variance {explained:.3f}")

    np.save(out / "embeddings.npy", reduced.astype(np.float16))
    df[["publication_number", "abstract_is_placeholder"]].to_parquet(out / "ids.parquet", index=False)

    meta = {
        "name": name,
        "method": "TF-IDF + TruncatedSVD (LSA), L2-normalised",
        "input": str(args.input),
        "n_publications": len(df),
        "text": "title_clean + ' ' + abstract_clean",
        "tfidf": {
            "lowercase": True,
            "strip_accents": "unicode",
            "stop_words": "english",
            "ngram_range": [1, args.ngram_max],
            "min_df": args.min_df,
            "max_df": args.max_df,
            "sublinear_tf": True,
            "vocabulary_size": int(vocab),
        },
        "svd": {
            "components": args.dims,
            "algorithm": "randomized",
            "n_iter": 7,
            "random_state": args.seed,
            "explained_variance_ratio_sum": explained,
        },
        "fitted_on": "full corpus",
        "storage_dtype": "float16",
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "seconds": round(time.time() - t0, 1),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[{name}] written to {out} in {meta['seconds']} s")


if __name__ == "__main__":
    main()
