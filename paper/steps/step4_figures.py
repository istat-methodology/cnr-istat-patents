#!/usr/bin/env python3
"""Step 4b - figures of the paper, in <run>/figures/ (.pdf for LaTeX, .png for a quick look).

One function per figure, each reads the CSV of one control:
  fig_reference_scale        c01  AMI against WIPO for reference partitions and models
  fig_cross_model            c02  ARI between models, seed-to-seed ARI on the diagonal
  fig_cn_removal             c03  full clustering vs refit: remove CN vs remove at random
  fig_explanation_stability  c04  Jaccard of the cluster cards across seeds, cohorts, models

Colours: blue = embedding model, orange = TF-IDF baseline, grey = reference partition.
Identity is also carried by marker shape and by the row label, never by colour alone.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402

BLUE, ORANGE, GREY, INK, MUTED = "#2a78d6", "#eb6834", "#8a8984", "#0b0b0b", "#52514e"

plt.rcParams.update({
    "font.size": 8, "axes.edgecolor": "#c9c8c3", "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": INK, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.axisbelow": True, "grid.color": "#ecebe7", "grid.linewidth": 0.6,
    "figure.facecolor": "white", "axes.facecolor": "white", "pdf.fonttype": 42,
})


def save(fig, folder: Path, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(folder / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def colour_of(model: str) -> str:
    return ORANGE if common.kind_of(model) == "baseline" else BLUE


def fig_reference_scale(run: Path, cfg: dict, folder: Path) -> None:
    data = pd.read_csv(run / "controls" / "c01_reference_scale.csv")
    data = data[data.cohort == "full"]
    fig, axes = plt.subplots(1, len(cfg["k"]), figsize=(7.2, 3.6), sharex=True, sharey=True)
    axes = np.atleast_1d(axes)
    first = data[data.k == cfg["k"][0]].set_index("partition")
    refs = [p for p in ["merge-oracle", "sector-oracle", "ipc-kmeans"] if p in first.index]
    ranked = first[first.kind != "reference"].sort_values("AMI_selection", ascending=False)
    order = refs + list(ranked.index) + (["random"] if "random" in first.index else [])
    labels = {"merge-oracle": "WIPO merged to K groups", "sector-oracle": "WIPO sectors (4)",
              "ipc-kmeans": "K-means on IPC only", "random": "Random labels"}
    for ax, k in zip(axes, cfg["k"]):
        d = data[data.k == k].set_index("partition")
        for i, name in enumerate(order):
            value = d.loc[name, "AMI_selection"]
            reference = name in labels
            ax.scatter(value, i, s=34, marker="s" if reference else "o", color=GREY if reference else colour_of(name),
                       zorder=3, edgecolor="white", linewidth=0.8)
            ax.text(value + 0.012, i, f"{value:.3f}", va="center", fontsize=6.5, color=MUTED)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([labels.get(n, common.pretty(n)) for n in order])
        ax.set_ylim(len(order) - 0.5, -0.5)
        ax.axvline(d.loc["merge-oracle", "AMI_selection"], color=GREY, lw=0.9, ls=(0, (4, 3)), zorder=1)
        ax.set_title(f"K = {k}", loc="left", fontsize=8.5, fontweight="bold")
        ax.set_xlabel("AMI against the WIPO field")
        ax.set_xlim(-0.02, 1.0)
        ax.grid(axis="y", visible=False)
    fig.text(0.0, -0.02, "Squares: reference partitions. Circles: K-means on model embeddings (blue) and on the TF-IDF baseline (orange). "
             "Dashed line: best coarsening of WIPO into K groups. Models are ordered by AMI at the first K.", fontsize=6.5, color=MUTED)
    fig.tight_layout()
    save(fig, folder, "fig_reference_scale")


def fig_cross_model(run: Path, cfg: dict, folder: Path) -> None:
    summary = pd.read_csv(run / "controls" / "c02_cross_model_summary.csv")
    fig, axes = plt.subplots(1, len(cfg["k"]), figsize=(7.4, 3.9))
    axes = np.atleast_1d(axes)
    image = None
    for ax, k in zip(axes, cfg["k"]):
        matrix = pd.read_csv(run / "controls" / f"c02_matrix_full_k{k}.csv", index_col=0)
        models = [m for m in cfg["deep_dive_models"] if m in matrix.index]
        models += [m for m in matrix.index if m not in models and common.kind_of(m) == "embedding"]
        models += [m for m in matrix.index if common.kind_of(m) == "baseline"]
        values = matrix.loc[models, models].to_numpy().copy()
        seed = summary[(summary.cohort == "full") & (summary.k == k)].set_index("model")["seed_ari"]
        for i, m in enumerate(models):
            values[i, i] = seed[m]
        image = ax.imshow(values, cmap="Blues", vmin=0, vmax=1)
        ax.grid(False)
        for i in range(len(models)):
            for j in range(len(models)):
                v = values[i, j]
                ax.text(j, i, f"{v:.2f}".lstrip("0") if v < 1 else "1", ha="center", va="center", fontsize=5.8,
                        color="white" if v > 0.6 else INK, fontweight="bold" if i == j else "normal")
        ax.add_patch(plt.Rectangle((-0.5, -0.5), 0, 0))
        ax.set_xticks(range(len(models)))
        ax.set_yticks(range(len(models)))
        ax.set_xticklabels([common.pretty(m) for m in models], rotation=60, ha="right", fontsize=6.5)
        ax.set_yticklabels([common.pretty(m) for m in models] if ax is axes[0] else [], fontsize=6.5)
        ax.set_title(f"K = {k}", loc="left", fontsize=8.5, fontweight="bold")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(length=0)
    cbar = fig.colorbar(image, ax=axes, fraction=0.025, pad=0.02)
    cbar.set_label("ARI", fontsize=7)
    cbar.ax.tick_params(labelsize=6.5)
    fig.text(0.0, -0.02, "Off-diagonal: ARI between the clusterings of two models. Bold diagonal: ARI between K-means seeds of the same model (noise ceiling).",
             fontsize=6.5, color=MUTED)
    save(fig, folder, "fig_cross_model")


def fig_cn_removal(run: Path, cfg: dict, folder: Path) -> None:
    data = pd.read_csv(run / "controls" / "c03_cn_vs_random.csv")
    fig, axes = plt.subplots(1, len(cfg["k"]), figsize=(7.2, 3.4), sharex=True, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, k in zip(axes, cfg["k"]):
        d = data[data.k == k]
        cn = d[d.scenario == "remove-CN"].set_index("model")["ARI_full_vs_refit"]
        rnd = d[d.scenario != "remove-CN"].groupby("model")["ARI_full_vs_refit"].agg(["mean", "min", "max"])
        if k == cfg["k"][0]:
            order = list(cn.sort_values().index)
        for i, m in enumerate(order):
            ax.plot([cn[m], rnd.loc[m, "mean"]], [i, i], color="#c9c8c3", lw=1.4, zorder=1)
            ax.plot([rnd.loc[m, "min"], rnd.loc[m, "max"]], [i, i], color=GREY, lw=2.2, alpha=0.5, zorder=2, solid_capstyle="round")
            ax.scatter(rnd.loc[m, "mean"], i, s=30, facecolor="white", edgecolor=GREY, linewidth=1.3, zorder=3)
            ax.scatter(cn[m], i, s=34, color=colour_of(m), zorder=4, edgecolor="white", linewidth=0.8)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([common.pretty(m) for m in order])
        ax.set_title(f"K = {k}", loc="left", fontsize=8.5, fontweight="bold")
        ax.set_xlabel("ARI, full clustering vs refit on the kept patents")
        ax.set_xlim(max(0.0, np.floor((data.ARI_full_vs_refit.min() - 0.05) * 10) / 10), 1.02)
        ax.set_ylim(len(order) - 0.5, -0.5)
        ax.grid(axis="y", visible=False)
    fig.text(0.0, -0.02, "Filled: CN removed. Open grey, with range over random draws: the same number of patents removed at random. "
             "Lower ARI = clusters move more.", fontsize=6.5, color=MUTED)
    fig.tight_layout()
    save(fig, folder, "fig_cn_removal")


def fig_explanation_stability(run: Path, cfg: dict, folder: Path) -> None:
    data = pd.read_csv(run / "controls" / "c04_explanation_summary.csv")
    fig, axes = plt.subplots(1, len(cfg["explain_k"]), figsize=(7.2, 3.6), sharex=True, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, k in zip(axes, cfg["explain_k"]):
        d = data[data.k == k]
        rows = []
        for kind, word in [("seed", "seeds"), ("cohort", "full vs no-CN")]:
            for m in cfg["deep_dive_models"]:
                s = d[(d.comparison == kind) & (d.model_a == m)]
                if len(s):
                    rows.append((f"{common.pretty(m)}, {word}", s.mean_jaccard_matched.mean(), s.min_jaccard_matched.min()))
        for _, r in d[d.comparison == "model"].iterrows():
            rows.append((f"{common.pretty(r.model_a)} vs {common.pretty(r.model_b)}", r.mean_jaccard_matched, r.min_jaccard_matched))
        null = d.mean_jaccard_unmatched.mean()
        for i, (label, mean, low) in enumerate(rows):
            ax.plot([low, mean], [i, i], color="#c9c8c3", lw=1.4, zorder=1)
            ax.scatter(low, i, s=14, marker="|", color=GREY, zorder=2)
            ax.scatter(mean, i, s=34, color=BLUE, zorder=3, edgecolor="white", linewidth=0.8)
            ax.text(mean + 0.02, i, f"{mean:.2f}", va="center", fontsize=6.5, color=MUTED)
        ax.axvline(null, color=GREY, lw=0.9, ls=(0, (4, 3)))
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r[0] for r in rows], fontsize=7)
        ax.set_ylim(len(rows) - 0.5, -0.5)
        ax.set_title(f"K = {k}", loc="left", fontsize=8.5, fontweight="bold")
        ax.set_xlabel("Jaccard of the top terms of matched clusters")
        ax.set_xlim(-0.02, 1.08)
        ax.grid(axis="y", visible=False)
    fig.text(0.0, -0.02, "Dot: mean over clusters (and over seed pairs). Tick: the least stable cluster. Dashed line: mean Jaccard of clusters that are not matched.",
             fontsize=6.5, color=MUTED)
    fig.tight_layout()
    save(fig, folder, "fig_explanation_stability")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    args = parser.parse_args()
    cfg = common.load_config(args.config)
    run = common.run_dir(cfg, args.quick)
    common.read_run_info(run)
    folder = run / "figures"
    for needed, function in [("c01_reference_scale.csv", fig_reference_scale), ("c02_cross_model_summary.csv", fig_cross_model),
                             ("c03_cn_vs_random.csv", fig_cn_removal), ("c04_explanation_summary.csv", fig_explanation_stability)]:
        if (run / "controls" / needed).exists():
            function(run, cfg, folder)
        else:
            print(f"skipped {function.__name__}: {needed} not found")
    print(f"figures in {folder}")
    print("step 4b done")


if __name__ == "__main__":
    main()
