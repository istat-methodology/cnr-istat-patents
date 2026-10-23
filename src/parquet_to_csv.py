#!/usr/bin/env python3
"""
parquet_to_csv.py
=================

Convert the merged Parquet files in ``data/processed/`` into CSV files,
optionally keeping only a random sample of the rows.

Why this script exists
----------------------
The repository ships the merged datasets as Parquet only: Parquet files are about
2.5 times smaller than CSV files and keep data types and lists, so the notebooks read them directly.
A CSV is still handy to open the data in Excel or in other tools, or to work on a small sample.
This script produces it in a few seconds.

What changes in the CSV
-----------------------
* dates are written as ``YYYY-MM-DD``;
* columns that hold lists in Parquet (``ipc_subclasses``, ``wipo_field_numbers``,
  ``wipo_field_names``, ``wipo_sectors``) become text with the items separated by ``;``,
  e.g. ``A61K;C12N``. Split them again with ``.str.split(";")`` when reading the CSV.

Usage
-----
Run it from the repository root.

    # convert both merged files (writes the CSV next to the Parquet files)
    python src/parquet_to_csv.py

    # convert one file
    python src/parquet_to_csv.py data/processed/patents_2021-2026_by_publication.parquet

    # random sample of 5,000 rows (reproducible with --seed), written to a separate folder
    python src/parquet_to_csv.py --sample 5000 --seed 42 --out-dir data/samples

With ``--sample N`` the file name gets the suffix ``_sampleN``, for example
``patents_2021-2026_by_publication_sample5000.csv``.

Options
-------
paths        Parquet files to convert (default: all ``patents_*.parquet`` in ``data/processed/``)
--out-dir    folder for the CSV files (default: the folder of each Parquet file)
--sample N   keep N random rows instead of all rows
--seed S     seed of the random sample (default 42)

Needs pandas and pyarrow (both in ``requirements.txt``). CSV files written in ``data/processed/``
are ignored by git (see ``.gitignore``).
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = ROOT / "data" / "processed"


def flatten(table: pd.DataFrame) -> pd.DataFrame:
    """Make a table CSV-friendly: lists -> ';'-separated text, datetimes -> YYYY-MM-DD."""
    out = table.copy()
    for col in out.columns:
        series = out[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            out[col] = series.dt.strftime("%Y-%m-%d")
        elif series.dtype == object and len(series) and isinstance(series.iloc[0], (list, tuple, np.ndarray)):
            out[col] = series.map(lambda items: ";".join(str(i) for i in items))
    return out


def convert(parquet_path: Path, out_dir: Path, sample: int = None, seed: int = 42) -> Path:
    table = pd.read_parquet(parquet_path)
    suffix = ""
    if sample is not None:
        if sample >= len(table):
            print(f"  note: sample ({sample}) is not smaller than the table ({len(table)} rows): keeping all rows")
        else:
            table = table.sample(n=sample, random_state=seed).sort_index()
            suffix = f"_sample{sample}"

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{parquet_path.stem}{suffix}.csv"
    flatten(table).to_csv(out_path, index=False)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert merged Parquet files to CSV, optionally on a random sample.")
    ap.add_argument("paths", nargs="*", type=Path, help="Parquet files (default: all in data/processed/)")
    ap.add_argument("--out-dir", type=Path, default=None, help="output folder (default: next to each Parquet file)")
    ap.add_argument("--sample", type=int, default=None, help="keep N random rows")
    ap.add_argument("--seed", type=int, default=42, help="seed for --sample (default 42)")
    args = ap.parse_args(argv)

    paths = args.paths or sorted(DEFAULT_DIR.glob("patents_*.parquet"))
    if not paths:
        sys.exit(f"No Parquet files found in {DEFAULT_DIR}. Run notebook 02_merge_and_clean first.")

    for p in paths:
        if not p.exists():
            sys.exit(f"File not found: {p}")
        out = convert(p, args.out_dir or p.parent, args.sample, args.seed)
        print(f"{p.name}  ->  {out}  ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
