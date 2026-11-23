#!/usr/bin/env python3
"""Step 1 - get the vectors of every model in config.yaml.

- Embedding models: downloaded from the public Hugging Face dataset
  (embeddings.npy, ids.parquet, meta.json per model). Already present = skipped.
- tfidf-svdNNN: built locally by src/generate_tfidf_baseline.py (a few minutes, CPU).

Result: <embeddings_dir>/<model>/{embeddings.npy, ids.parquet, meta.json}
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def present(folder: Path) -> bool:
    return (folder / "embeddings.npy").exists() and (folder / "ids.parquet").exists()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    args = parser.parse_args()
    cfg = common.load_config(args.config)
    emb_dir: Path = cfg["embeddings_dir"]
    emb_dir.mkdir(parents=True, exist_ok=True)

    for model in cfg["models"]:
        if present(emb_dir / model):
            print(f"[{model}] already in {emb_dir}")
            continue
        if model.startswith("tfidf-svd"):
            dims = int(model.removeprefix("tfidf-svd"))
            print(f"[{model}] building the lexical baseline")
            subprocess.run(
                [
                    sys.executable, str(common.REPO / "src" / "generate_tfidf_baseline.py"),
                    "--input", str(cfg["data"]), "--out-dir", str(emb_dir),
                    "--name", model, "--dims", str(dims),
                ],
                check=True,
            )
            continue
        from huggingface_hub import hf_hub_download

        print(f"[{model}] downloading from {cfg['hf_dataset']}")
        for filename in ["embeddings.npy", "ids.parquet", "meta.json"]:
            try:
                hf_hub_download(
                    cfg["hf_dataset"], f"{model}/{filename}", repo_type="dataset",
                    revision=cfg.get("hf_revision"), local_dir=str(emb_dir),
                )
            except Exception as error:  # meta.json is nice to have, the other two are required
                if filename != "meta.json":
                    raise
                print(f"[{model}] {filename} not downloaded: {error}")
        if not present(emb_dir / model):
            raise FileNotFoundError(f"{model}: download incomplete in {emb_dir / model}")
    print("step 1 done")


if __name__ == "__main__":
    main()
