#!/usr/bin/env python3
"""Step 5 - results pack for the co-authors: <run>/brian_pack/

Reads paper/results_registry.yaml and, for every result marked done, copies its tables
(.tex and .csv) and writes INDEX.md: the question, the message, and the table as markdown.
A co-author opens INDEX.md and has everything, with the files next to it.

The `message` of each result is written by hand in the registry, after reading the run.
INDEX.md states which run the tables come from.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def markdown_table(frame: pd.DataFrame, decimals: int = 3) -> str:
    cells = frame.copy()
    for column in cells.columns:
        if pd.api.types.is_float_dtype(cells[column]):
            cells[column] = cells[column].map(lambda v: "" if pd.isna(v) else f"{v:.{decimals}f}")
    header = "| " + " | ".join(map(str, cells.columns)) + " |"
    rule = "|" + "|".join("---" for _ in cells.columns) + "|"
    body = ["| " + " | ".join(map(str, row)) + " |" for row in cells.itertuples(index=False)]
    return "\n".join([header, rule, *body])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    args = parser.parse_args()
    cfg = common.load_config(args.config)
    run = common.run_dir(cfg, args.quick)
    common.read_run_info(run)
    registry = yaml.safe_load((common.PAPER_DIR / "results_registry.yaml").read_text(encoding="utf-8"))

    pack = run / "brian_pack"
    tables_out = pack / "tables"
    tables_out.mkdir(parents=True, exist_ok=True)
    rc = json.loads((run / "run_config.json").read_text(encoding="utf-8"))

    lines = [
        "# Results pack",
        "",
        f"Run: `{run.name}`. Created {rc.get('created_utc', '')[:10]}. "
        f"numpy {rc.get('numpy_version')}, pandas {rc.get('pandas_version')}, scikit-learn {rc.get('sklearn_version')}.",
        f"Models: {', '.join(rc['models'])}.",
        f"K: {rc['k_values']}. Seeds: {rc['seeds']}. Cohorts: {rc['cohorts']}.",
        "",
        "Level is a proposal: workshop = short paper, journal = extended version.",
        "",
        "| Id | Result | Level | Status |",
        "|---|---|---|---|",
    ]
    for r in registry:
        lines.append(f"| {r['id']} | {r['title']} | {r['level']} | {r['status']} |")
    lines.append("")

    for r in registry:
        lines += [f"## {r['id']} {r['title']}", "", f"Level: {r['level']}. Status: {r['status']}.", "",
                  f"Question: {r['question']}", ""]
        if r.get("message"):
            lines += [f"Message: {' '.join(str(r['message']).split())}", ""]
        lines += [f"Script: `{r['script']}`", ""]
        for name in r.get("tables", []):
            csv = run / "paper_tables" / f"{name}.csv"
            if not csv.exists():
                lines += [f"Table `{name}`: not found in this run.", ""]
                continue
            for ext in ("csv", "tex"):
                shutil.copy(run / "paper_tables" / f"{name}.{ext}", tables_out / f"{name}.{ext}")
            lines += [f"Table `{name}` (files: `tables/{name}.tex`, `tables/{name}.csv`)", "",
                      markdown_table(pd.read_csv(csv)), ""]
    (pack / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"pack in {pack}")
    print("step 5 done")


if __name__ == "__main__":
    main()
