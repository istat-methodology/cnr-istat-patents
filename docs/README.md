# Documentation guide

This repository contains three related but distinct kinds of material. Use this page to find the current source of truth for each one.

## Research project

- [Research status](research-status.md) — current dataset, analysis design, preliminary results, caveats, and next steps for the paper.
- [Methodology](methodology.md) — corpus construction, WIPO–IPC concordance, sampling, and known dataset limits.
- [WIPO technology fields glossary](wipo-technology-fields.csv) — concise Italian descriptions of all 35 WIPO fields; fields 33–35 are outside this corpus.
- [Cluster label review](cluster-label-review.md) — first-pass labels and evidence-based comments for the Qwen 4B, SBERT and Pat-SPECTER K=8 clusters.
- [Workflow](workflow.md) — how the source data, embeddings, notebooks, and analysis scripts fit together.
- [Data dictionary](data_dictionary.md) — dataset columns and known issues.
- [Embeddings](embeddings.md) — model inputs, outputs, model IDs, and generation details.
- [Full-corpus analysis instructions](../analysis/README.md) — how to reproduce the K-means analysis from precomputed embeddings.
- [Three-model comparison page](model-comparison.html) — local interactive comparison of Qwen 4B, Patent SBERT-adapt-ub, and Pat-SPECTER.
- [WIPO cluster-profile comparison](../analysis/results/run_20261118T132255Z/comparison/wipo_cluster_comparison_full_k8.md) — prevalence and weighted-Jaccard heatmaps for the three paper models, with interpretation and ARI context.

## Existing exploratory dashboard

- [Patent Observatory](patent-observatory/README.md) — Brian's broader dashboard and the analyses assembled from notebooks 13 and 14. Its scope and outputs are kept separate from the three-model comparison page.

## Canonical analysis outputs

The committed full-corpus run is [`analysis/results/run_20261118T132255Z/`](../analysis/results/run_20261118T132255Z/). Its `run_config.json` records the parameters; `metrics/`, `audit/`, `assignments/`, and `profiles/` hold the clustering outputs. The `comparison/` subfolder contains post-processed WIPO profile heatmaps and pairwise cluster-profile similarities; these use saved profiles and do not refit the clustering. The research-status document summarizes selected results and links back to these files.

