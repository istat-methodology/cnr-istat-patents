# Paper plan

Working document for the workshop paper and its extended version. It is meant to bring a new
collaborator, or a new chat, up to date. The numbers come from the run `paper-2026-11`
(`paper/outputs/paper-2026-11/`). The registry of results is `results_registry.yaml`, in this folder.

## Two levels

1. **Workshop short paper** (Istat methodology workshop, second week of December 2026, English, 8-10 pages).
   It introduces the collaboration with the university and presents the audit protocol on this corpus.
   The proceedings carry little scientific weight, so the paper is a first, reduced version of the work.
2. **Extended version for a journal** (journal not chosen yet). New title, a hand-labelled sample,
   a validation of the controls on known defects, and a literature section. A small labelling effort is
   enough; a large annotation campaign with students is planned for next year, separately.

All simulations are run and recorded once. The workshop paper uses the subset of results marked
`workshop` in the registry. The rest is kept for the journal.

## Story (A): an audit protocol for embedding clusters without ground truth

The corpus has no ground truth for the clusters. WIPO fields exist but are not the target. The protocol
asks five questions of any clustering of patent embeddings:

| Control | Question | Script |
|---|---|---|
| Alignment with a reference | How much of WIPO does the clustering recover, on a scale with floor and ceiling? | `c01_reference_scale.py` |
| Cross-model agreement | Do different models find the same clusters, relative to seed noise? | `c02_noise_ceiling.py` |
| Confounders | Is a metadata variable (office, CN) driving the clusters? | `c03_confounder_cn.py` |
| Stability | Are clusters and their explanations stable across seeds, cohorts and models? | `c03`, `c04_explanation_stability.py` |
| Explanation cards | Does a card (c-TF-IDF terms, examples, WIPO profile) describe the cluster faithfully? | `c04`, planned `c05` |

The tone is methodological, with an explainable-AI framing: the cluster card is the explanation, and the
controls test whether it can be trusted. The literature search on evaluation of clustering and on
explanation of unsupervised models has not been done yet.

## Data and models

- Corpus: 63,968 WIPO32 patent publications 2021-2026 (CN 67.8%, 20,579 without CN).
- Eight embedding models plus a TF-IDF + SVD(256) baseline. Deep-dive models, with cluster cards and
  manual review: Qwen3-Embedding-4B (general-purpose, with a clustering instruction), Patent SBERT-adapt-ub
  (domain-adapted), Pat-SPECTER (SPECTER2 fine-tuned on patents).
- Other models: BGE-M3, Qwen3-Embedding-0.6B, EmbeddingGemma-300m, PaECTER, MPNet.
- K-means (k-means++, n_init 10, max_iter 300), K = 8 and 16, seeds 42-44, cohorts full and exclude-CN.
- Embeddings: Hugging Face dataset `istat-ai/wipo32-patent-embeddings`. The TF-IDF baseline is built by
  `src/generate_tfidf_baseline.py`, fitted once on the full corpus.

## Results so far (run `paper-2026-11`, K=8 unless stated)

- AMI against WIPO: models 0.27-0.34, TF-IDF 0.25. Best coarsening of WIPO into 8 groups: 0.750. IPC-only
  K-means: 0.314 (K=8), 0.419 (K=16), above every model at K=16.
- Qwen3-4B is the outlier on cross-model agreement (mean ARI 0.28) and the most sensitive to office
  (AMI office 0.164; TF-IDF 0.170, the other models 0.03-0.08).
- Pat-SPECTER and PaECTER are the closest pair (ARI 0.68).
- Several models are not stable across seeds at K=8 (gemma 0.80, PaECTER 0.78, mpnet 0.84, TF-IDF 0.84,
  BGE-M3 0.87). The three deep-dive models and Qwen3-0.6B are at 0.997 or above.
- Removing CN moves the clusters more than removing the same number of patents at random (ARI between the
  full clustering and the refit 0.40-0.88 against 0.66-0.98). The AMI against WIPO on the same patents
  changes little after the refit.
- Inside each office the AMI against WIPO stays at 0.25-0.39. CN is the lowest for all models.
- Cluster cards are identical across seeds at K=8, differ strongly between full and exclude-CN
  (term Jaccard 0.13-0.22), and overlap weakly between models (0.10-0.24).

## Conventions

- Source of the numbers of the paper: the pipeline in `paper/`. Notebooks are exploratory.
- AMI against office uses the raw office code, as `analysis/run_analysis.py`. The within-office analysis
  uses seven groups (CN, US, WO, EP, JP, KR, Other), as Notebook 13.
- A rerun with the same settings of the earlier run `run_20261118T132255Z` agrees to the third or fourth
  decimal and not bit by bit. The difference is attributed to the number of threads.
- The statement "excluding CN raises the AMI against WIPO" refers to different sets of patents. On the
  same patents the refit gains little (control 3). It should be worded accordingly.

## Environment

Azure VM with an A100 and 24 cores. Python 3.10.12, numpy 2.2.6, pandas 2.3.3, scikit-learn 1.7.2.
The clustering runs on CPU. The GPU is for the instruction-prefix ablation (R10).
Local overrides (threads, explanation K) go in `paper/config.local.yaml`, not in git.

## How to run

```bash
python paper/run.py --quick          # test on a sample
python paper/run.py                  # full pipeline
python paper/run.py --step pack      # results pack for the co-authors
```

See `paper/README.md`.

## Workflow

- Mauro and Claude run the simulations and record them in the registry.
- Brian writes the paper. He reads `paper/outputs/<run>/brian_pack/INDEX.md`: for each result, the question,
  the message, the table in markdown, and the `.tex` and `.csv` files next to it.
- Mauro and Brian choose together which results go in the workshop paper.

## Open points

- Submission deadline of the short paper and the date by which Brian needs the materials.
- Journal for the extended version.
- Which registry results go in the workshop paper (current column `level` is a proposal).
- Controls still to write: surrogate fidelity (R08), boundary ambiguity (R09), prefix ablation (R10).
- Hand-labelled sample and validation on known defects (R11).
- Literature on evaluation of clusters without ground truth and on explainable AI for unsupervised models.
- Pat-SPECTER manual review.
