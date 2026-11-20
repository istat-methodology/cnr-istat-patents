# Confronto dei profili WIPO nei cluster — full, K=8

## Materiali

- Heatmap prevalenza WIPO: [`wipo_cluster_profiles_full_k8.svg`](wipo_cluster_profiles_full_k8.svg)
- Heatmap similarità profili: [`wipo_cluster_overlap_full_k8.svg`](wipo_cluster_overlap_full_k8.svg)
- Prevalenze per cluster e campo: [`wipo_cluster_profiles_full_k8.csv`](wipo_cluster_profiles_full_k8.csv)
- Similarità per coppia di cluster: [`wipo_cluster_similarity_full_k8.csv`](wipo_cluster_similarity_full_k8.csv)

## Come leggere il confronto

La prevalenza è la quota di brevetti del cluster con almeno un IPC compatibile con il campo WIPO. I campi sono multi-label, quindi le quote per riga non sommano a 100%. La similarità tra due profili usa il weighted Jaccard sulle 32 prevalenze: 0 indica nessuna prevalenza condivisa, 1 profili identici. Le matrici non forzano una corrispondenza 1:1 tra cluster.

Questa è una comparazione descrittiva dei profili WIPO. Non misura direttamente se gli stessi brevetti siano raggruppati insieme: per l’accordo sulle assegnazioni va letto insieme all’ARI tra modelli. La coorte è stratificata per field WIPO, quindi l’allineamento ai campi non è una validazione indipendente.

## Coppie con maggiore sovrapposizione

| Modelli | Cluster | Weighted Jaccard | Campi con prevalenza alta in entrambi (A / B) |
|---|---:|---:|---|
| Qwen 4B × SBERT | 3 ↔ 0 | 0.826 | Macromolecular chemistry, polymers (28.2% / 30.0%), Materials, metallurgy (24.7% / 27.5%), Basic materials chemistry (24.0% / 26.3%) |
| Qwen 4B × SBERT | 0 ↔ 5 | 0.772 | Pharmaceuticals (49.0% / 48.5%), Biotechnology (41.0% / 44.9%), Organic fine chemistry (20.4% / 23.1%) |
| Qwen 4B × SBERT | 2 ↔ 2 | 0.690 | Semiconductors (38.3% / 26.5%), Optics (25.1% / 26.3%), Audio-visual technology (15.6% / 15.1%) |
| Qwen 4B × Pat-SPECTER | 3 ↔ 3 | 0.794 | Macromolecular chemistry, polymers (28.2% / 30.8%), Materials, metallurgy (24.7% / 25.9%), Basic materials chemistry (24.0% / 26.4%) |
| Qwen 4B × Pat-SPECTER | 2 ↔ 0 | 0.747 | Semiconductors (38.3% / 31.8%), Optics (25.1% / 28.2%), Audio-visual technology (15.6% / 16.1%) |
| Qwen 4B × Pat-SPECTER | 5 ↔ 6 | 0.683 | Computer technology (43.1% / 45.1%), Digital communication (41.1% / 28.7%), IT methods for management (23.4% / 26.7%) |
| SBERT × Pat-SPECTER | 4 ↔ 6 | 0.937 | Computer technology (44.4% / 45.1%), Digital communication (27.8% / 28.7%), IT methods for management (26.1% / 26.7%) |
| SBERT × Pat-SPECTER | 6 ↔ 2 | 0.899 | Basic communication processes (34.9% / 36.6%), Telecommunications (21.8% / 20.6%), Electrical machinery, apparatus, energy (23.1% / 19.9%) |
| SBERT × Pat-SPECTER | 0 ↔ 3 | 0.883 | Macromolecular chemistry, polymers (30.0% / 30.8%), Basic materials chemistry (26.3% / 26.4%), Materials, metallurgy (27.5% / 25.9%) |

## Accordo sulle assegnazioni

Il weighted Jaccard confronta la forma dei profili WIPO, mentre l’ARI confronta quali brevetti finiscono insieme nei due clustering. Sono misure diverse: profili WIPO simili possono coesistere con un accordo più limitato sulle assegnazioni.

| Modelli | ARI (seed 42) |
|---|---:|
| Qwen 4B × SBERT | 0.282 |
| Qwen 4B × Pat-SPECTER | 0.276 |
| SBERT × Pat-SPECTER | 0.487 |

## Fonti

- Profili salvati nel run: `profiles/full__<model>__k8__wipo_profiles.csv`.
- Glossario dei campi: [`../../../../docs/wipo-technology-fields.csv`](../../../../docs/wipo-technology-fields.csv).
- Metriche ARI tra modelli: `metrics/cross_model_ari_reference_seed.csv`.
