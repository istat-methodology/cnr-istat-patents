# References for the workshop paper

First list, from a web search on 2026-11-24. Titles and identifiers come from the search results.
Authors, venue and pages are marked "check" where the result did not show them; check them before they go in the `.bib`.
Entries are grouped by the place they have in the paper.

## 1. Evaluating clusters without ground truth (protocol, controls 1-3)

- Vinh, Epps, Bailey (2010). *Information Theoretic Measures for Clusterings Comparison: Variants, Properties, Normalization and Correction for Chance.* JMLR 11, 2837-2854. https://jmlr.csail.mit.edu/beta/papers/v11/vinh10a.html
  Use: definition of AMI and why the correction for chance is needed when K is small against the number of labels (our K=8, 16 against 32 WIPO fields).
- Romano, Vinh, Bailey, Verspoor. *Adjusting for Chance Clustering Comparison Measures.* arXiv:1512.01286. Check venue and year (JMLR). https://arxiv.org/abs/1512.01286
  Use: ARI and AMI adjusted for chance; supports reading the AMI against the random partition (control 1, floor).
- *The Impact of Random Models on Clustering Similarity.* arXiv:1701.06508, JMLR 18 (2017). Check authors. https://arxiv.org/abs/1701.06508
  Use: the value 0 of an adjusted measure depends on the random model; relevant to the reference scale of control 1.
- von Luxburg (2010). *Clustering Stability: An Overview.* arXiv:1007.1075. Check venue (Foundations and Trends in Machine Learning). https://arxiv.org/abs/1007.1075
  Use: stability as the main tool when there is no ground truth; frames controls 2 and 4.
- *Stability estimation for unsupervised clustering: A review.* WIREs Data Mining and Knowledge Discovery 14(6), Nov 2022. Check authors. https://pubmed.ncbi.nlm.nih.gov/36583207/
  Use: recent review of stability, with open questions.
- Ullmann, Hennig, Boulesteix (2021). *Validation of cluster analysis results on validation data: A systematic framework.* WIREs Data Mining and Knowledge Discovery, e1444. doi:10.1002/widm.1444. https://arxiv.org/abs/2103.01281
  Use: structure of internal, external and stability validation; a place to position the five controls.
- Mourer, Forest, Lebbah, Azzag, Lacaille. *Selecting the Number of Clusters K with a Stability Trade-off: an Internal Validation Criterion.* arXiv:2006.08530. https://arxiv.org/abs/2006.08530
  Use: example of stability-based validation of K-means.
- Silva et al. (2022). *No Pattern, No Recognition: a Survey about Reproducibility and Distortion Issues of Text Clustering and Topic Modeling.* arXiv:2208.01712. Check author list. https://arxiv.org/abs/2208.01712
  Use: initialisation and outlier effects on text clustering; background for seed stability (control 2).

## 2. Explaining clusters and embeddings (framing, controls 4-5)

- Hu, Jiang, Dong, Liu, He. *Interpretable Clustering: A Survey.* arXiv:2409.00743 (v3, Oct 2025); ACM Computing Surveys 58, doi:10.1145/3789495. https://arxiv.org/abs/2409.00743
  Use: taxonomy of explainable clustering; our cluster cards are post-hoc explanations, not interpretable-by-design methods.
- *Interpretable Text Embeddings and Text Similarity Explanation: A Survey.* arXiv:2502.14862. Check authors. https://arxiv.org/abs/2502.14862
  Use: explanation of embedding similarity; places our work next to this line.
- Survey on explainable clustering in the Journal of Intelligent Systems, doi:10.1515/jisys-2024-0477. Check authors and title. https://www.degruyterbrill.com/document/doi/10.1515/jisys-2024-0477/pdf
  Use: second survey, categorises methods by how the explanation is generated.
- Adadi, Berrada (2018). *Peeking inside the black-box: A survey on explainable artificial intelligence (XAI).* IEEE Access 6, 52138-52160. Found as a reference inside the Hu et al. survey; check.
  Use: general XAI reference.
- Grootendorst (2022). *BERTopic: Neural topic modeling with a class-based TF-IDF procedure.* arXiv:2203.05794. https://arxiv.org/abs/2203.05794
  Use: the c-TF-IDF cluster cards are this procedure; the cite for the card method.

## 3. Patent embeddings and models used

- Ghosh, Erhardt, Rose, Buunk, Harhoff (2024). *PaECTER: Patent-level Representation Learning using Citation-informed Transformers.* arXiv:2402.19411. https://arxiv.org/abs/2402.19411
- *Tracing the Flow of Knowledge From Science to Technology Using Deep Learning* (Pat-SPECTER). arXiv:2512.24259. Check authors. https://arxiv.org/abs/2512.24259
  Note: the paper cautions that cosine similarities of Pat-SPECTER embeddings cluster around 0.86; relevant to our silhouette values.
- Patent SBERT-adapt-ub: arXiv:2403.16630, compares static and contextual embeddings on patent interferences (cited as Sarra et al. 2024 in a 2026 benchmark). Check title and authors. https://arxiv.org/abs/2403.16630
- Zhang et al. (2025). *Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models.* arXiv:2506.05176. https://arxiv.org/abs/2506.05176
  Use: Qwen3-Embedding-0.6B and 4B; the models are instruction-aware (relevant to the prefix ablation, R10).
- Yousefiramandi, Cooney (2026). *Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering.* arXiv:2605.24297. https://arxiv.org/abs/2605.24297
  Use: closest related work. It evaluates clustering of patent embeddings against labels (K-means with K set to the number of labels; V-measure, ARI, NMI) and finds Qwen3-0.6B the best by ARI. We have no ground truth and audit the clusters instead.

## 4. WIPO technology fields

- Schmoch (2008). *Concept of a Technology Classification for Country Comparisons.* Final report to WIPO. https://wipo.int/documents/2948119/3215563/wipo_ipc_technology.pdf
- WIPO. *IPC - Technology Concordance Table.* Revised January 2013. https://ideas.repec.org/c/wip/eccode/8.html
  Note: the table has 35 fields; the pipeline uses fields 1-32 (`analysis/run_analysis.py`). The paper should say so.

## Still to search

Not yet searched, so not listed above:
- SPECTER and SPECTER2 papers, BGE-M3, EmbeddingGemma, MPNet (model citations).
- Foundations of XAI beyond the surveys (for example Doshi-Velez and Kim on evaluating interpretability).
- Faithfulness and human evaluation of topic labels and cluster descriptions, including labels written by LLMs.
- Use of patent classification schemes as proxy ground truth, and criticism of it.
- Official statistics: classification of patents or products with embeddings (for the Istat audience).
