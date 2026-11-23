#!/usr/bin/env python3
"""Run the paper pipeline from the repository root.

    python paper/run.py --quick                # test everything on a small sample (minutes)
    python paper/run.py                        # the full pipeline
    python paper/run.py --step cluster         # one step only
    python paper/run.py --step controls --only c01

Steps, in order:
    embeddings   get the vectors of every model (Hugging Face + TF-IDF baseline)
    cluster      K-means for every model, cohort, K, seed (analysis/run_analysis.py)
    controls     one script per control, in paper/controls/
    report       tables for the paper, in <run>/paper_tables/

Settings are in paper/config.yaml. Results are in paper/outputs/<run_name>/.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = {
    "embeddings": "step1_embeddings.py",
    "cluster": "step2_cluster.py",
    "controls": "step3_controls.py",
    "report": "step4_report.py",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--step", choices=["all", *STEPS], default="all")
    parser.add_argument("--config", type=Path, default=HERE / "config.yaml")
    parser.add_argument("--quick", action="store_true", help="Small random sample, to test the pipeline")
    parser.add_argument("--only", nargs="+", help="With --step controls: run only these controls")
    parser.add_argument("--dry-run", action="store_true", help="With --step cluster: print the engine command and stop")
    args = parser.parse_args()

    chosen = list(STEPS) if args.step == "all" else [args.step]
    for step in chosen:
        script = HERE / "steps" / STEPS[step]
        command = [sys.executable, str(script), "--config", str(args.config)]
        if args.quick:
            command.append("--quick")
        if step == "controls" and args.only:
            command += ["--only", *args.only]
        if step == "cluster" and args.dry_run:
            command.append("--dry-run")
        print(f"=== {step}")
        subprocess.run(command, check=True)
    print("done")


if __name__ == "__main__":
    main()
