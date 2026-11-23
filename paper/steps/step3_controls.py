#!/usr/bin/env python3
"""Step 3 - run the control scripts in paper/controls/ (c01_*.py, c02_*.py, ...).

Each control answers one question and writes its own CSV in
<output_dir>/<run_name>/controls/. Controls can also be run one by one:

    python paper/controls/c01_reference_scale.py [--quick]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common.add_common_args(parser)
    parser.add_argument("--only", nargs="+", help="Run only these controls, e.g. --only c01 c02")
    args = parser.parse_args()

    scripts = sorted((common.PAPER_DIR / "controls").glob("c[0-9][0-9]_*.py"))
    if args.only:
        scripts = [s for s in scripts if s.name[:3] in args.only]
    for script in scripts:
        print(f"--- {script.name}")
        command = [sys.executable, str(script), "--config", str(args.config)]
        if args.quick:
            command.append("--quick")
        subprocess.run(command, check=True)
    print("step 3 done")


if __name__ == "__main__":
    main()
