# Paper pipeline

Scripts that produce the tables (and later the figures) of the workshop paper.
They are separate from the exploratory notebooks and from `analysis/`: this folder
only calls `analysis/run_analysis.py` and adds the controls described in the paper.

## Run

From the repository root, with Python 3.10+ and `pip install -r analysis/requirements.txt pyyaml huggingface_hub`:

```bash
python paper/run.py --quick     # test on 3,000 patents, a few minutes, numbers are not results
python paper/run.py             # full pipeline (about 1-2 h on a CPU machine; resumable)
python paper/run.py --step cluster      # one step: embeddings | cluster | controls | report | pack
python paper/run.py --step controls --only c01
```

All settings (models, K, seeds, cohorts, paths) are in `paper/config.yaml`.
Machine-specific values (for example `threads`) go in `paper/config.local.yaml`, which overrides `config.yaml` and is not in git.
The results of the pipeline are listed in `paper/results_registry.yaml`; the plan is in `docs/paper-plan.md`.
Results go to `paper/outputs/<run_name>/` (not in git).

## Steps

| Step | Script | What it does |
|---|---|---|
| 1 `embeddings` | `steps/step1_embeddings.py` | downloads the vectors from Hugging Face (`istat-ai/wipo32-patent-embeddings`) and builds the TF-IDF + SVD baseline |
| 2 `cluster` | `steps/step2_cluster.py` | K-means for each model, cohort (full, exclude-CN), K and seed, with `analysis/run_analysis.py` |
| 3 `controls` | `controls/c0N_*.py` | one script per control, each writes a CSV in `<run>/controls/` |
| 4 `report` | `steps/step4_report.py` | collects the tables of the paper in `<run>/paper_tables/` (`.csv` and `.tex`) |
| 5 `pack` | `steps/step5_pack.py` | results pack for the co-authors in `<run>/brian_pack/`: `INDEX.md` with question, message and table of each result, plus the tables |

## Controls

| Script | Question |
|---|---|
| `c01_reference_scale.py` | What AMI vs WIPO can a partition reach? Random, sector oracle, merge oracle, IPC-only K-means, models |
| `c02_noise_ceiling.py` | How much do models agree, relative to the seed-to-seed noise ceiling? |
| `c03_confounder_cn.py` | Is CN a confounder or just a smaller sample? Remove CN vs remove the same number at random; AMI inside each office |
| `c04_explanation_stability.py` | Are the c-TF-IDF cluster cards stable across seeds, cohorts and models? (deep-dive models, K=8) |

More controls are added here as they are agreed (surrogate, boundary cases).
Controls 3 and 4 refit K-means (about 20-40 minutes on a 24-core machine).

## Notes

- `--quick` samples publications at random and slices every embedding matrix, then uses the same code and settings.
- AMI vs office uses the raw `office` code (as `analysis/run_analysis.py`). Notebook 13 groups offices in 7 classes, so its values differ slightly (e.g. Qwen 0.162 vs 0.164).
- The TF-IDF baseline is fitted once on the full corpus; the exclude-CN cohort reuses the same vectors.
- Reference run with the same settings: `analysis/results/run_20261118T132255Z`. The full run should reproduce it.
