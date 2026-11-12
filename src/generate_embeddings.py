#!/usr/bin/env python
"""Generate embeddings of patent title + abstract with several models.

Reads the merged one-row-per-publication table and, for every model,
writes a folder  embeddings/<model>/  with:

    embeddings.npy   float16, shape (n_patents, dim), L2-normalised
    ids.parquet      publication_number (+ abstract_is_placeholder), same row order
    meta.json        model id, revision, dtype, prompt, max length, truncation stats, library versions

Rules:
- Input text = title + abstract (the joiner is a per-model setting).
- No chunking: each text is truncated at the model's max length (see MODELS).
  In this corpus only ~0.04% of abstracts exceed 512 tokens; `meta.json` reports the exact count.
- The forward pass runs in fp32 (encoders) or bf16 (Gemma, Qwen). Embeddings are stored as float16.
- The run resumes: embeddings are computed in shards, finished shards are kept, finished models are skipped.

Usage (from the repository root):
    python src/generate_embeddings.py --list
    python src/generate_embeddings.py --models sbert-adapt-ub --limit 200 --out-dir /tmp/emb_test   # smoke test
    python src/generate_embeddings.py                                                             # all models
    python src/generate_embeddings.py --models qwen3-embedding-4b bge-m3
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "patents_2021-2026_by_publication.parquet"
DEFAULT_OUT = ROOT / "embeddings"
SHARD_SIZE = 8192

QWEN_INSTRUCTION = (
    "Instruct: Given the title and abstract of a patent, "
    "represent it for clustering by technology field\nQuery:"
)


@dataclass
class ModelSpec:
    hf_id: str
    max_seq_length: int                  # truncation limit used for this model
    compute_dtype: str = "float32"       # float32 | bfloat16
    batch_size: int = 64
    joiner: str = " "                    # between title and abstract
    prompt: str | None = None            # literal prefix, passed to encode(prompt=...)
    prompt_name: str | None = None       # name in the model's own prompts dict
    tokenizer_kwargs: dict = field(default_factory=dict)
    note: str = ""


MODELS: dict[str, ModelSpec] = {
    "embeddinggemma-2": ModelSpec(
        "google/embeddinggemma-2", 2048, "bfloat16", 64,
        prompt_name="Clustering",        # "task: clustering | query: "
        note="fp16 compute gives NaN on this model: use bf16 or fp32. Needs sentence-transformers>=6.1.0",
    ),
    "bge-m3": ModelSpec("BAAI/bge-m3", 2048, "float32", 64, note="dense embedding, CLS pooling, no prompt"),
    "qwen3-embedding-4b": ModelSpec(
        "Qwen/Qwen3-Embedding-4B", 2048, "bfloat16", 32,
        prompt=QWEN_INSTRUCTION, tokenizer_kwargs={"padding_side": "left"},
        note="instruction prefix on every text, last-token pooling",
    ),
    "paecter": ModelSpec("mpi-inno-comp/paecter", 512, "float32", 128),
    "pat-specter": ModelSpec(
        "mpi-inno-comp/pat_specter", 512, "float32", 128,
        joiner=" [SEP] ", note="SPECTER convention: title [SEP] abstract; CLS pooling",
    ),
    "sbert-adapt-ub": ModelSpec("graziasveva93/sbert-adapt-ub", 512, "float32", 128),
}


def build_texts(df: pd.DataFrame, joiner: str) -> list[str]:
    title = df["title_clean"].fillna("").astype(str).str.strip()
    abstract = df["abstract_clean"].fillna("").astype(str).str.strip()
    return (title + joiner + abstract).str.strip().tolist()


def load_model(spec: ModelSpec, device: str):
    import torch
    from sentence_transformers import SentenceTransformer

    dtype = getattr(torch, spec.compute_dtype)
    attn = None
    if spec.hf_id.startswith("Qwen/"):
        attn = "flash_attention_2" if importlib.util.find_spec("flash_attn") else "sdpa"

    last_err = None
    for dtype_key in ("dtype", "torch_dtype"):     # name changed across transformers versions
        model_kwargs = {dtype_key: dtype}
        if attn:
            model_kwargs["attn_implementation"] = attn
        try:
            model = SentenceTransformer(
                spec.hf_id, device=device, model_kwargs=model_kwargs,
                tokenizer_kwargs=spec.tokenizer_kwargs or None,
            )
            break
        except (TypeError, ValueError) as e:
            last_err = e
    else:
        raise last_err
    model.max_seq_length = spec.max_seq_length
    return model


def token_stats(model, texts: list[str], prefix: str, max_len: int) -> dict:
    tok = model.tokenizer
    lens = []
    for i in range(0, len(texts), 4096):
        batch = [prefix + t for t in texts[i:i + 4096]]
        ids = tok(batch, add_special_tokens=True, truncation=False)["input_ids"]
        lens.extend(len(x) for x in ids)
    lens = np.asarray(lens)
    return {
        "tokens_mean": round(float(lens.mean()), 1),
        "tokens_p99": int(np.percentile(lens, 99)),
        "tokens_max": int(lens.max()),
        "n_truncated": int((lens > max_len).sum()),
    }


def run_model(name: str, spec: ModelSpec, df: pd.DataFrame, out_root: Path, device: str,
              batch_size: int | None, overwrite: bool) -> None:
    import torch

    out = out_root / name
    if (out / "meta.json").exists() and (out / "embeddings.npy").exists() and not overwrite:
        print(f"[{name}] already done, skipping (use --overwrite to redo)")
        return
    out.mkdir(parents=True, exist_ok=True)
    shard_dir = out / "_shards"
    if overwrite:
        shutil.rmtree(shard_dir, ignore_errors=True)
    shard_dir.mkdir(exist_ok=True)

    print(f"[{name}] loading {spec.hf_id} ({spec.compute_dtype}) on {device}")
    t0 = time.time()
    model = load_model(spec, device)

    prompt = spec.prompt
    if spec.prompt_name:
        prompt = model.prompts[spec.prompt_name]       # resolved string, stored in meta.json
    texts = build_texts(df, spec.joiner)
    stats = token_stats(model, texts, prompt or "", spec.max_seq_length)
    print(f"[{name}] prompt={prompt!r} max_len={spec.max_seq_length} {stats}")

    bs = batch_size or spec.batch_size
    n = len(texts)
    n_shards = (n + SHARD_SIZE - 1) // SHARD_SIZE
    for k in range(n_shards):
        path = shard_dir / f"{k:05d}.npy"
        if path.exists():
            continue
        chunk = texts[k * SHARD_SIZE:(k + 1) * SHARD_SIZE]
        emb = model.encode(
            chunk, batch_size=bs, prompt=prompt, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=True,
        )
        if not np.isfinite(emb).all():
            raise RuntimeError(f"[{name}] NaN/inf in shard {k}: check dtype")
        tmp = shard_dir / f"{k:05d}.tmp.npy"
        np.save(tmp, emb.astype(np.float16))
        os.replace(tmp, path)
        print(f"[{name}] shard {k + 1}/{n_shards} done")

    emb = np.concatenate([np.load(shard_dir / f"{k:05d}.npy") for k in range(n_shards)])
    assert emb.shape[0] == n, (emb.shape, n)
    np.save(out / "embeddings.npy", emb)
    df[["publication_number", "abstract_is_placeholder"]].to_parquet(out / "ids.parquet", index=False)

    try:
        revision = model[0].auto_model.config._commit_hash
    except Exception:
        revision = None
    import sentence_transformers, transformers
    meta = {
        "model": name, "hf_id": spec.hf_id, "revision": revision,
        "n_patents": n, "dim": int(emb.shape[1]), "stored_dtype": "float16", "normalized": True,
        "compute_dtype": spec.compute_dtype, "max_seq_length": spec.max_seq_length,
        "joiner": spec.joiner, "prompt": prompt, "prompt_name": spec.prompt_name,
        "chunking": "none (truncation at max_seq_length)", **stats,
        "seconds": round(time.time() - t0), "batch_size": bs, "note": spec.note,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "versions": {"torch": torch.__version__, "sentence_transformers": sentence_transformers.__version__,
                     "transformers": transformers.__version__, "python": platform.python_version()},
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    shutil.rmtree(shard_dir, ignore_errors=True)
    print(f"[{name}] saved {emb.shape} in {meta['seconds']} s -> {out}")

    del model
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--device", default=None, help="default: cuda if available, else cpu")
    ap.add_argument("--batch-size", type=int, default=None, help="override the per-model default")
    ap.add_argument("--limit", type=int, default=None, help="use only the first N patents (smoke test)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--list", action="store_true", help="print the model registry and exit")
    args = ap.parse_args()

    if args.list:
        for k, s in MODELS.items():
            print(f"{k:20s} {s.hf_id:35s} max_len={s.max_seq_length:5d} {s.compute_dtype:9s} {s.note}")
        return

    import torch
    torch.backends.cuda.matmul.allow_tf32 = True
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    df = pd.read_parquet(args.input, columns=["publication_number", "title_clean", "abstract_clean",
                                              "abstract_is_placeholder"])
    assert df["publication_number"].is_unique, "publication_number must be unique"
    if args.limit:
        df = df.head(args.limit)
    df = df.reset_index(drop=True)
    print(f"{len(df)} patents from {args.input.name}; output in {args.out_dir}")

    for name in args.models:
        run_model(name, MODELS[name], df, args.out_dir, device, args.batch_size, args.overwrite)


if __name__ == "__main__":
    main()
