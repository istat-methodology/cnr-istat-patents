#!/usr/bin/env python3
"""Step 4 - collect the tables of the paper in <run>/paper_tables/ (.csv and .tex).

Each table is one function below, so it is clear which file feeds which table.
Figures will be added here.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def order(frame: pd.DataFrame, cfg: dict, column: str = "model") -> pd.DataFrame:
    rank = {m: i for i, m in enumerate(cfg["deep_dive_models"] + [m for m in cfg["models"] if m not in cfg["deep_dive_models"]])}
    return frame.assign(_o=frame[column].map(rank)).sort_values("_o").drop(columns="_o")


def table_models(run: Path, cfg: dict, cohort: str, k: int) -> pd.DataFrame:
    """Per model: AMI vs WIPO, AMI vs office, silhouette, seed ARI, full vs no-CN ARI."""
    m = pd.read_csv(run / "metrics" / "model_k_summary.csv")
    m = m[(m.cohort == cohort) & (m.k == k)]
    out = m[["model", "AMI_WIPO_selection_primary_mean", "AMI_office_mean", "silhouette_mean", "seed_ARI_mean"]].copy()
    out.columns = ["Model", "AMI WIPO", "AMI office", "Silhouette", "Seed ARI"]
    refit = run / "metrics" / "full_vs_no_cn_refit_ari.csv"
    if refit.exists():
        r = pd.read_csv(refit)
        r = r[r.k == k].groupby("model")["ARI_full_fit_vs_no_cn_refit"].mean()
        out["ARI full vs no-CN"] = out["Model"].map(r)
    return order(out, cfg, "Model")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    args = parser.parse_args()
    cfg = common.load_config(args.config)
    run = common.run_dir(cfg, args.quick)
    common.read_run_info(run)
    out = run / "paper_tables"

    for k in cfg["k"]:
        common.write_table(table_models(run, cfg, "full", k), out, f"tab_models_full_k{k}")
    c1 = run / "controls" / "c01_reference_scale.csv"
    if c1.exists():
        t = pd.read_csv(c1)
        t = t[t.cohort == "full"][["k", "partition", "AMI_selection", "AMI_office", "share_of_merge_oracle"]]
        common.write_table(t, out, "tab_reference_scale")
    c2 = run / "controls" / "c02_cross_model_summary.csv"
    if c2.exists():
        t = pd.read_csv(c2)
        t = t[t.cohort == "full"][["k", "model", "seed_ari", "mean_ari_vs_others", "max_ari", "closest_model"]]
        common.write_table(order(t, cfg), out, "tab_cross_model")
    print(f"tables in {out}")
    print("step 4 done")


if __name__ == "__main__":
    main()
