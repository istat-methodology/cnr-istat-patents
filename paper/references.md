# References for the workshop paper

List built from web searches on 2026-11-24. Titles and identifiers come from the search results or from the arXiv and ACL pages.
Authors, venue and pages are marked "check" where the sources did not show them; check them before they go in the `.bib`.
Sections 5 to 8 were added on the same day.
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
- Rose, Ghosh, Erhardt, Li, Buunk, Harhoff (2025). *Tracing the Flow of Knowledge From Science to Technology Using Deep Learning* (Pat-SPECTER). arXiv:2512.24259, submitted 30 Dec 2025. https://arxiv.org/abs/2512.24259
  Note: the paper cautions that cosine similarities of Pat-SPECTER embeddings cluster around 0.86; relevant to our silhouette values.
- Ascione, Sterzi (2024). *A comparative analysis of embedding models for patent similarity.* arXiv:2403.16630. Introduces Patent SBERT-adapt-ub. https://arxiv.org/abs/2403.16630
  Note: an earlier note in this file cited it as Sarra et al. 2024, from a 2026 benchmark; the arXiv page gives Ascione and Sterzi. Use the arXiv authors, and check if a journal version exists.
- Zhang et al. (2025). *Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models.* arXiv:2506.05176. https://arxiv.org/abs/2506.05176
  Use: Qwen3-Embedding-0.6B and 4B; the models are instruction-aware (relevant to the prefix ablation, R10).
- Yousefiramandi, Cooney (2026). *Benchmarking Patent Embeddings: A Multi-Task Evaluation of 22 Models Across Retrieval, Classification, and Clustering.* arXiv:2605.24297. https://arxiv.org/abs/2605.24297
  Use: closest related work. It evaluates clustering of patent embeddings against labels (K-means with K set to the number of labels; V-measure, ARI, NMI) and finds Qwen3-0.6B the best by ARI. We have no ground truth and audit the clusters instead.

## 4. WIPO technology fields

- Schmoch (2008). *Concept of a Technology Classification for Country Comparisons.* Final report to WIPO. https://wipo.int/documents/2948119/3215563/wipo_ipc_technology.pdf
- WIPO. *IPC - Technology Concordance Table.* Revised January 2013. https://ideas.repec.org/c/wip/eccode/8.html
  Note: the table has 35 fields; the pipeline uses fields 1-32 (`analysis/run_analysis.py`). The paper should say so.

## 5. Other embedding models in the study

- Cohan, Feldman, Beltagy, Downey, Weld (2020). *SPECTER: Document-level Representation Learning using Citation-informed Transformers.* ACL 2020, pp. 2270-2282. doi:10.18653/v1/2020.acl-main.207. https://aclanthology.org/2020.acl-main.207
  Use: origin of the `title [SEP] abstract` input convention used for Pat-SPECTER and PaECTER.
- Singh, D'Arcy, Cohan, Downey, Feldman (2023). *SciRepEval: A Multi-Format Benchmark for Scientific Document Representations.* EMNLP 2023, pp. 5548-5566. doi:10.18653/v1/2023.emnlp-main.338. arXiv:2211.13308. https://aclanthology.org/2023.emnlp-main.338
  Use: the paper that releases SPECTER2. Pat-SPECTER is described as SPECTER2 fine-tuned on patents (Rose et al. 2025).
- Chen, Xiao, Zhang, Luo, Lian, Liu (2024). *BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation.* arXiv:2402.03216 (v4, 28 Jun 2024). Check whether a venue version exists. https://arxiv.org/abs/2402.03216
- Schechter Vera, Dua, Zhang, Salz et al. (2025). *EmbeddingGemma: Powerful and Lightweight Text Representations.* arXiv:2509.20354 (v3, 1 Nov 2025). 308M parameters, built on Gemma 3. https://arxiv.org/abs/2509.20354
- Song, Tan, Qin, Lu, Liu (2020). *MPNet: Masked and Permuted Pre-training for Language Understanding.* NeurIPS 33. arXiv:2004.09297. https://proceedings.neurips.cc/paper/2020/hash/c3a690be93aa602ee2dc0ccab5b7b67e-Abstract.html
- Reimers, Gurevych (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP-IJCNLP 2019, pp. 3982-3992. doi:10.18653/v1/D19-1410. https://aclanthology.org/D19-1410
  Note: the `mpnet` model of the pipeline is `sentence-transformers/all-mpnet-base-v2` (`docs/embeddings.md`). That is an MPNet encoder fine-tuned for sentence embeddings, so cite Song et al. for the encoder and Reimers and Gurevych for the sentence-transformers framework. The model card, not found here, should be checked for the fine-tuning data.

## 6. Evaluating and labelling clusters and topics

- Doshi-Velez, Kim (2017). *Towards A Rigorous Science of Interpretable Machine Learning.* arXiv:1702.08608. https://arxiv.org/abs/1702.08608
  Use: taxonomy of evaluation (application-grounded, human-grounded, functionally-grounded). The cluster card sits in the human-grounded case; the Jaccard of control 4 is a functionally-grounded proxy.
- Lau, Grieser, Newman, Baldwin (2011). *Automatic Labelling of Topic Models.* ACL 2011, pp. 1536-1545. https://aclanthology.org/P11-1154/
  Use: early evaluation framework for topic labels with human judgements.
- Hoyle, Goel, Hian-Cheong, Peskov, Boyd-Graber, Resnik (2021). *Is Automated Topic Model Evaluation Broken? The Incoherence of Coherence.* NeurIPS 2021. arXiv:2107.02173. https://arxiv.org/abs/2107.02173
  Use: automatic coherence scores need validation against human judgement; supports the plan of a hand-labelled sample (R11).
- Doogan, Buntine (2021). *Topic Model or Topic Twaddle? Re-evaluating Semantic Interpretability Measures.* NAACL 2021. https://aclanthology.org/people/caitlin-doogan
  Use: same point for specialised collections, with open labelling by humans. Check the page range and the anthology ID.
- *ProxAnn: Use-Oriented Evaluations of Topic Models and Document Clustering.* arXiv:2507.00828 (2025). Check authors and venue; the code is at github.com/ahoho/proxann. https://arxiv.org/abs/2507.00828
  Use: protocol where an annotator, or an LLM as a proxy, reads documents of a cluster, infers a category and applies it to other documents. Close to what a card should support; candidate method for R11.
- Trainin, Abend (2025). *T5Score: A Methodology for Automatically Assessing the Quality of LLM Generated Multi-Document Topic Sets.* arXiv:2407.17390 (v3, May 2025). Check authors and venue. https://arxiv.org/abs/2407.17390
  Use: evaluation of topic sets written by LLMs; relevant only if the journal version adds LLM-written labels.

## 7. IPC and WIPO fields as reference labels

What was found supports the point in general terms. A source on the consistency of IPC assignment between offices is still missing (see the last section).

- Zhang, Zhong, Yuan (2019). *A Critical Note on the Evaluation of Clustering Algorithms.* arXiv:1908.03782. Check the venue (ECAI 2020?). https://arxiv.org/abs/1908.03782
  Use: classification labels taken as ground truth for clustering are a common shortcut with consequences for the conclusions. General, not about patents.
- Joyce, Raff (2021). *A Framework for Cluster and Classifier Evaluation in the Absence of Reference Labels.* arXiv:2109.11126. Check the venue. https://arxiv.org/abs/2109.11126
  Use: evaluation when the reference labels are of lower quality; bounds on metrics. Relevant to the circularity of IPC-only references (R02).
- Filippi-Mazzola, Bianchi, Wit (2022). *Drivers of the decrease of patent similarities from 1976 to 2021.* arXiv:2212.06046 (v3, Mar 2023). https://arxiv.org/abs/2212.06046
  Use: the full text has a passage stating that institutional classification schemes are not a reliable picture of patent similarity. The abstract page does not show it, so read the passage in the PDF before citing.
- Yousefiramandi, Cooney (2026), already in section 3, uses classification labels as the clustering target; our protocol is the alternative when this is not appropriate.
- Possible: arXiv:2610.12997, *Benchmarking Embedding Geometries and Clustering Algorithms for Unsupervised Patent Claim Classification.* Only a fragment was seen, saying that the labels are not a direct measure of technical similarity. Read it before deciding.

## 8. Official statistics and the link between patents and industries

- Bruno, Di Zio, Ortame (2025). *Language Models for Automated Coding in Official Statistics: Risks and Opportunities.* 4th Workshop on Methodologies for Official Statistics, Istat, Proceedings. https://www.istat.it/wp-content/uploads/2025/11/abstract-2_Bruno.pdf
  Use: the authors' own line of work on semantic search for NACE coding, with the same concerns on interpretability. Check the proceedings version and pages.
- Vidali, Jean, Le Pera (2024). *Unlocking NACE Classification Embeddings with OpenAI for Enhanced Analysis and Processing.* arXiv:2409.11524. Check affiliation and venue. https://arxiv.org/abs/2409.11524
  Use: embeddings of a statistical classification, seen from the statistical side.
- ESS and AIML4OS, Work Package 10, *From text to code*, on NACE, COICOP and ISCO coding. https://cros.ec.europa.eu/book-page/aiml4os-wp10-text-code-experiences-and-potential-use-aiml-classifying-and-coding
  Use: context for the official-statistics audience. A web page, not a paper; cite as a project page or leave it out.
- Lybbert, Zolas (2014). *Getting patents and economic data to speak to each other: An 'Algorithmic Links with Probabilities' approach for joint analyses of patenting and economic activity.* Research Policy 43(3), 530-542. https://econpapers.repec.org/RePEc:eee:respol:v:43:y:2014:i:3:p:530-542
  Use: concordance between IPC and industry classifications built with text. Background for the BRUNO pipeline that maps patents to NACE.
- Dorner, Harhoff (2017). *A Novel Technology-Industry Concordance Table Based on Linked Inventor-Establishment Data.* FDZ-Methodenreport 07/2017, IAB. https://doku.iab.de/fdz/reporte/2017/MR_07-17_EN.pdf
- Fraunhofer ISI (2019). Discussion paper 60/2019, on concordance tables between WIPO35 technology fields and NACE Rev. 2 sectors. Check authors and title. https://isi.fraunhofer.de/content/dam/isi/dokumente/ccp/innovation-systems-policy-analysis/2019/discussionpaper_60_2019.pdf
  Use of the last two: a statistical office needs patents by industry. The concordances go through IPC, which links back to the circularity of the WIPO reference.

## Still open

- No source found on the inconsistency of IPC or CPC assignment between offices or examiners. One search returned a 1980s study with a very low IPC consistency between US and UK examiners (inlibra.com, not identifiable). Another option is the OECD patent report already in `papers/`. A search on patent classification consistency in scientometrics and patent-analytics journals is needed.
- Further work on human evaluation of explanations is not listed. Doshi-Velez and Kim may be enough for a short paper.
- Faithfulness of term-based explanations (surrogate models, R08) belongs to the journal version.
- Eurostat or national statistical office work on patents classified by embeddings was not found. The Istat workshop paper and the AIML4OS page are the closest.
