# Conference paper: results outline

*Working note for converging on the story. This is a focused account of the current three-model comparison, separate from the Patent Observatory. Manual review of cluster examples remains to be completed.*

## Working title

**Do patent embedding models tell the same story? A focused comparison on a WIPO-stratified corpus**

## Proposed research question

**On a fixed WIPO32 patent corpus, how much do three text embedding models agree in the clusters they produce, how strongly do those clusters align with the WIPO sampling fields, and how sensitive are these patterns to the corpus's office composition?**

This asks about model dependence, alignment with the corpus design, and sensitivity to office composition. It does not ask which model recovers the “true” technological taxonomy. Whether cluster profiles and patent examples are coherent on human inspection remains an open interpretive question.

## Scope

- Briefly introduce the corpus: 32 WIPO fields, 2,000 selections per field, 63,968 distinct publications after deduplication. The sample is stratified by WIPO field, not representative of global patenting.
- Focus on **Qwen3-Embedding-4B**, **Patent SBERT-adapt-ub**, and **Pat-SPECTER**.
- Use **K=8** as the main comparison because it is the level used for comparable cluster cards. Treat K=16 as sensitivity, not a second main story.
- Compare the complete corpus with the existing **exclude-CN refit** as a sensitivity analysis, not as a causal estimate of a country effect.
- Keep Brian's **Patent Observatory** separate. It is a broader exploratory dashboard from earlier notebook analyses, with additional models and methods; do not pool its results with this comparison.

## Results to organize the paper around

### 1. All three models show association with WIPO labels, at different levels

On the complete corpus at K=8, mean AMI with the WIPO selection field across three seeds is 0.285 for Qwen 4B, 0.327 for SBERT-adapt-ub, and 0.315 for Pat-SPECTER. AMI with the primary IPC-compatible WIPO field is 0.296, 0.330, and 0.311, respectively.

These labels are linked to the sampling and IPC–WIPO concordance design. AMI is not independent validation of semantic quality.

### 2. The models produce different partitions

For the complete corpus, pairwise ARI between model partitions at K=8 (seed 42) ranges from 0.276 to 0.487. The models are not producing identical clusters under different names.

### 3. The observed structure changes with office composition

After refitting without CN, mean WIPO-selection AMI is 0.383 for Qwen 4B, 0.352 for SBERT-adapt-ub, and 0.354 for Pat-SPECTER. On the 20,579 shared publications, ARI between full-corpus and exclude-CN assignments is 0.646, 0.740, and 0.876, respectively.

Describe this as sensitivity to corpus composition and refitting. Qwen's lower seed stability in the exclude-CN cohort (mean ARI 0.865) also cautions against reading its higher WIPO AMI alone.

### 4. Cluster cards and patent examples support interpretation

Use a small, comparable set of cards and patent examples to show clear profiles, overlaps, and ambiguous boundaries. Complete the planned human review before making claims about interpretability or coherence. Apply the same selection rule across models and include central, boundary, and conflicting examples rather than only persuasive cases.

## Measures

- **Primary comparison:** AMI with the WIPO selection field, explicitly identified as the sampling label.
- **Robustness check:** AMI with the primary IPC-compatible WIPO field; the lowest-numbered compatible field is a convention to reduce a multi-field match to one label.
- **Partition comparison:** ARI between models and between full and exclude-CN refits.
- **Geometry:** cosine silhouette is descriptive context, not a model ranking, because embedding spaces differ.
- **WIPO overlap:** the current mean is **1.75 compatible WIPO fields per publication**. Use as corpus context, not the headline finding.

## Supported claims

- All three selected embeddings produce K-means partitions with measurable association to the WIPO design labels.
- The detailed partition depends on the embedding model.
- Measured structure and stability vary between the full and exclude-CN cohorts.
- The results motivate targeted human inspection of cluster cards and patent examples.

## Claims to avoid

- A model is globally superior based on AMI or silhouette alone.
- The clusters recover a unique or objectively correct technology taxonomy.
- WIPO AMI is independent expert validation.
- Excluding CN estimates a causal effect or makes the remaining sample representative.
- The three-model comparison subsumes Brian's Patent Observatory.
- Cluster interpretability is validated before the planned patent review.

## Provisional conclusion

In this WIPO-stratified patent corpus, three text embedding models yield cluster partitions associated with the WIPO sampling structure but different in their assignments. The observed patterns also vary when office composition changes. This supports a model-dependent and composition-sensitive view of patent clustering, while interpretation of individual clusters remains subject to targeted human review.

## Repository sources

- [Research status](research-status.md)
- [Analysis protocol](../analysis/README.md)
- [Canonical run configuration](../analysis/results/run_20261118T132255Z/run_config.json)
- [Canonical run metrics](../analysis/results/run_20261118T132255Z/metrics/model_k_summary.csv)
- [Patent Observatory overview](patent-observatory/README.md)
