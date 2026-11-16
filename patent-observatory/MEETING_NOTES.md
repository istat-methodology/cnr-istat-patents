# ISTAT–CNR — suggested brief explanation for the meeting

## The question

"Does our WIPO-stratified patent sample contain meaningful semantic heterogeneity, and does this conclusion depend on the embedding model or clustering method?"

## Evidence, in order

1. **Sampling design:** 64,000 technology-field selections across 32 WIPO fields, 63,968 distinct publications after publication-level deduplication; four sectors. This *design* ensures coverage across the chosen fields, but does not by itself prove semantic separation.
2. **Nine representations:** Mauro published eight new models on Hugging Face, aligned by patent ID. The prior chunked MiniLM is the ninth baseline. All were clustered on the same 63,968 patents at K=8/16.
3. **Technological signal:** All nine representations show positive same-WIPO versus different-WIPO cosine similarity advantages within office groups in the 6,400-patent pilot. The full K-Means partitions also have positive WIPO AMI.
4. **Granularity and robustness:** More clusters tend to increase WIPO AMI while lowering silhouette or initialization stability. Ordinary and spherical K-Means have similar external correspondence, but do not assign each patent identically. HDBSCAN left most patents unassigned under the tested PCA50 parameter settings.
5. **Interpretation via real documents:** Open a map, hover, click a central or peripheral patent, and discuss how cluster membership can be coherent at the center yet ambiguous at its edges.

## A concise conclusion (EN)

"We find measurable technological differentiation across the WIPO-stratified patent corpus, broadly robust across multiple text embeddings. However, the detailed partition is sensitive to the representation, K and clustering method, and office-related structure remains a confounder for some models. These findings support a technologically diverse dataset with overlapping domains, but not a unique natural taxonomy nor a claim of higher diversity than an older sample without direct comparison."

## Una versione breve (IT)

"Le analisi indicano una differenziazione tecnologica misurabile del campione, osservata con nove rappresentazioni vettoriali e verificata con più strategie di clustering. I raggruppamenti più generali sono relativamente robusti, mentre le suddivisioni fini dipendono maggiormente dal modello e dai parametri. Per alcuni embedding osserviamo anche una componente associata all'ufficio brevettuale. Possiamo quindi descrivere il campione come tecnologicamente diversificato, ma non dimostrare una tassonomia unica né che sia più eterogeneo del campione precedente senza un confronto diretto."

## How to interpret the visuals

- UMAP projects embeddings into two dimensions for human exploration; the appearance of islands is **not** a formal clustering metric.
- The pilot maps show 2,400 matched patent IDs, not all 63,968. Each model has its own projection.
- The dashboard's per-model centroid-distance plots show the selected review candidates (not the whole corpus or UMAP coordinates).
- When clicking peripheral examples, do not call a patent "wrong" unless its technological content has been evaluated. Multi-technology inventions are common.
