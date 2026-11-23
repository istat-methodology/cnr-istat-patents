"""Shared helpers for the paper pipeline.

Everything that more than one script needs lives here: reading the config,
locating the run folder, the WIPO sector of a field, a LaTeX table writer.
The corpus loaders are the ones of analysis/run_analysis.py, imported as `engine`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

PAPER_DIR = Path(__file__).resolve().parent
REPO = PAPER_DIR.parent
sys.path.insert(0, str(REPO / "analysis"))
import run_analysis as engine  # noqa: E402  (corpus loaders and WIPO matching)

DEFAULT_CONFIG = PAPER_DIR / "config.yaml"

# WIPO sectors of fields 1-32 (docs/methodology.md, section 3).
SECTOR_RANGES = {
    "Electrical engineering": range(1, 9),
    "Instruments": range(9, 14),
    "Chemistry": range(14, 25),
    "Mechanical engineering": range(25, 33),
}
SECTOR_OF_FIELD = {f: s for s, fields in SECTOR_RANGES.items() for f in fields}


def sector_of(field: int) -> str:
    return SECTOR_OF_FIELD[int(field)]


def add_common_args(parser) -> None:
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to config.yaml")
    parser.add_argument("--quick", action="store_true", help="Small random sample, to test the pipeline in minutes")


def load_config(path: Path | None = None) -> dict:
    cfg = yaml.safe_load(Path(path or DEFAULT_CONFIG).read_text(encoding="utf-8"))
    for key in ["data", "concordance", "embeddings_dir", "output_dir"]:
        cfg[key] = (REPO / cfg[key]).resolve()
    return cfg


def run_name(cfg: dict, quick: bool) -> str:
    return cfg["run_name"] + ("-quick" if quick else "")


def run_dir(cfg: dict, quick: bool) -> Path:
    return cfg["output_dir"] / run_name(cfg, quick)


def read_run_info(run: Path) -> dict:
    """What step 2 recorded about the run: which corpus and embeddings it used."""
    path = run / "paper_run.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: run step 'cluster' first")
    return json.loads(path.read_text(encoding="utf-8"))


def assignment_files(run: Path) -> list[tuple[str, str, Path]]:
    """(cohort, model, path) for every assignment file written by the engine."""
    found = []
    for path in sorted((run / "assignments").glob("*.parquet")):
        cohort, model = path.stem.split("__", 1)
        found.append((cohort, model, path))
    return found


def kind_of(source: str) -> str:
    return "baseline" if source.startswith("tfidf") else "embedding"


def _latex_escape(value) -> str:
    text = str(value)
    for old, new in [("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#")]:
        text = text.replace(old, new)
    return text


def write_table(frame: pd.DataFrame, folder: Path, name: str, decimals: int = 3) -> None:
    """Write <name>.csv and <name>.tex (booktabs, no caption: the paper adds it)."""
    folder.mkdir(parents=True, exist_ok=True)
    frame.to_csv(folder / f"{name}.csv", index=False)
    cells = frame.copy()
    for column in cells.columns:
        if pd.api.types.is_float_dtype(cells[column]):
            cells[column] = cells[column].map(lambda v: "" if pd.isna(v) else f"{v:.{decimals}f}")
    lines = [
        "\\begin{tabular}{" + "l" * len(cells.columns) + "}",
        "\\toprule",
        " & ".join(_latex_escape(c) for c in cells.columns) + " \\\\",
        "\\midrule",
    ]
    for row in cells.itertuples(index=False):
        lines.append(" & ".join(_latex_escape(v) for v in row) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    (folder / f"{name}.tex").write_text("\n".join(lines), encoding="utf-8")
