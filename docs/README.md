# Documentation guide

This repository contains three related but distinct kinds of material. Use this page to find the current source of truth for each one.

## Research project

- [Research status](research-status.md) — current dataset, analysis design, preliminary results, caveats, and next steps for the paper.
- [Methodology](methodology.md) — corpus construction, WIPO–IPC concordance, sampling, and known dataset limits.
- [Workflow](workflow.md) — how the source data, embeddings, notebooks, and analysis scripts fit together.
- [Data dictionary](data_dictionary.md) — dataset columns and known issues.
- [Embeddings](embeddings.md) — model inputs, outputs, model IDs, and generation details.
- [Full-corpus analysis instructions](../analysis/README.md) — how to reproduce the K-means analysis from precomputed embeddings.
- [Three-model comparison page](model-comparison.html) — local interactive comparison of Qwen 4B, Patent SBERT-adapt-ub, and Pat-SPECTER.

## Existing exploratory dashboard

- [Patent Observatory](patent-observatory/README.md) — Brian's broader dashboard and the analyses assembled from notebooks 13 and 14. Its scope and outputs are kept separate from the three-model comparison page.

## Canonical analysis outputs

The committed full-corpus run is [`analysis/results/run_20261118T132255Z/`](../analysis/results/run_20261118T132255Z/). Its `run_config.json` records the parameters; `metrics/`, `audit/`, `assignments/`, and `profiles/` hold the derived outputs. The research-status document summarizes selected results and links back to these files.

