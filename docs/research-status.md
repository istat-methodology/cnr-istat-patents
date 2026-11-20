# Stato della ricerca: brevetti WIPO32

**Fotografia aggiornata al 20 novembre 2026.** Questo documento serve a preparare il paper e la discussione con Brian. Riassume risultati esplorativi; non è ancora un testo di risultati finali né una validazione esperta dei cluster.

## 1. Domanda di ricerca, in forma provvisoria

Il lavoro studia se le rappresentazioni testuali dei brevetti del corpus WIPO32 organizzano i documenti in cluster interpretabili e in che misura il risultato dipende dall'embedding, dalla granularità K e dalla forte composizione geografica del campione.

La domanda non è ancora formulata come test di una tassonomia tecnologica “vera”. Il campione è costruito per coprire 32 campi WIPO; non è un campione casuale della popolazione mondiale dei brevetti.

## 2. Dataset e classificazione

- Le quattro query BigQuery applicano la concordanza IPC–Technology della WIPO ai campi **1–32**: 2.000 selezioni per ciascun campo, 64.000 righe a livello di selezione.
- Dopo la deduplicazione per numero di pubblicazione, il corpus usato dagli embedding contiene **63.968 pubblicazioni distinte**. L'intervallo definito dalle query è 1 gennaio 2021–30 settembre 2026; l'ultima data osservata indicata nella documentazione del dataset è 17 settembre 2026.
- I 32 campi appartengono a quattro dei cinque settori WIPO. Il settore “Other fields” e i campi 33–35 non sono inclusi.
- La pubblicazione conserva tutti i codici IPC disponibili. Nel run di audit la media è **4,19 codici IPC** per pubblicazione, la mediana è 3 e l'86,9% ha almeno due codici.
- Applicando tutte le regole WIPO ai codici IPC di ogni pubblicazione, si ottiene una media di **1,75 campi compatibili**; il 53,6% delle pubblicazioni è compatibile con almeno due campi. Questo è il risultato del run corrente (`audit/corpus_overview.csv`), da usare al posto del valore 1,28 discusso in precedenza finché non ne viene chiarita la diversa definizione o provenienza.
- Il campo WIPO di selezione descrive il disegno del campione; la compatibilità calcolata dagli IPC descrive quali altri campi le regole consentono. Non sono la stessa variabile. Per una pubblicazione selezionata in più campi, l'AMI richiede una singola etichetta: l'analisi usa convenzionalmente il campo con numero più basso e riporta separatamente i profili multi-campo.
- **CN rappresenta il 67,8%** del corpus (43.389 pubblicazioni). Escludendo l'ufficio CN restano **20.579** pubblicazioni. Questa coorte è un'analisi di sensibilità sostanziale, non un nuovo campione riequilibrato per campo.
- L'unità è la pubblicazione, non la famiglia brevettuale: la stessa invenzione può apparire in più uffici. Uffici, tipi di documento e codici kind sono misti. I kind code non hanno significato uniforme tra uffici; inoltre il prefisso CN identifica l'ufficio di pubblicazione, non il paese dell'inventore, del richiedente o della priorità.

Dettagli e fonti: [metodologia del corpus](methodology.md), [dizionario dati](data_dictionary.md), [concordanza WIPO e query](workflow.md).

## 3. Disegno dell'analisi corrente

Gli embedding di titolo e abstract sono precomputati e disponibili nel dataset pubblico [Hugging Face `istat-ai/wipo32-patent-embeddings`](https://huggingface.co/datasets/istat-ai/wipo32-patent-embeddings). Il run completo analizza otto modelli; la pagina comparativa mette in primo piano i tre selezionati per la discussione: **Qwen3-Embedding-4B**, **Patent SBERT-adapt-ub** e **Pat-SPECTER**.

La pipeline corrente è [`analysis/run_analysis.py`](../analysis/run_analysis.py). Nel run `run_20261118T132255Z`:

- i vettori float16 sono riallineati ai numeri di pubblicazione, convertiti in float32 e normalizzati L2;
- K-means standard (Lloyd, inizializzazione k-means++, `n_init=10`, massimo 300 iterazioni) è stimato per **K=8 e K=16**, con seed **42, 43, 44**;
- la silhouette è calcolata con distanza coseno su un campione deterministico di 1.200 pubblicazioni per coorte e modello;
- sono calcolati AMI con il WIPO di selezione, AMI con il WIPO compatibile primario (campo compatibile dal numero più basso), AMI con l'ufficio, ARI tra seed, ARI tra modelli e ARI tra i fit full e senza CN;
- le card descrivono i cluster con termini **c-TF-IDF** da titolo e abstract, composizione WIPO e IPC, uffici e brevetti vicini al centroide; sono inclusi anche esempi di frontiera.

Il clustering assegna ogni pubblicazione a un solo cluster, mentre la compatibilità WIPO può essere multipla. c-TF-IDF significa *class-based term frequency–inverse document frequency*: qui è un descrittore lessicale dei cluster, non un modello separato che assegna topic o prova da solo la coerenza semantica.

## 4. Risultati preliminari: K=8 e tre modelli

Le metriche sotto sono medie dei tre seed. La silhouette usa il campione da 1.200; gli AMI sono calcolati sull'intera coorte. `AMI WIPO selezione` usa l'etichetta di disegno convenzionale; `AMI WIPO IPC primario` usa la singola etichetta compatibile scelta con la regola del numero minimo.

| Coorte | Modello | N | Silhouette coseno | AMI WIPO selezione | AMI WIPO IPC primario | ARI medio fra seed |
|---|---|---:|---:|---:|---:|---:|
| Completa | Qwen 4B | 63.968 | 0,132 | 0,285 | 0,296 | 0,999 |
| Completa | SBERT-adapt-ub | 63.968 | 0,257 | 0,327 | 0,330 | 0,997 |
| Completa | Pat-SPECTER | 63.968 | 0,146 | 0,315 | 0,311 | 0,999 |
| Senza CN | Qwen 4B | 20.579 | 0,170 | 0,383 | 0,388 | 0,865 |
| Senza CN | SBERT-adapt-ub | 20.579 | 0,302 | 0,352 | 0,359 | 0,995 |
| Senza CN | Pat-SPECTER | 20.579 | 0,145 | 0,354 | 0,347 | 0,995 |

Altri confronti sul seed 42:

| Confronto delle partizioni K=8 | Corpus completo | Senza CN |
|---|---:|---:|
| Qwen 4B vs SBERT-adapt-ub | 0,282 | 0,381 |
| Qwen 4B vs Pat-SPECTER | 0,276 | 0,409 |
| SBERT-adapt-ub vs Pat-SPECTER | 0,487 | 0,527 |

ARI fra fit full e senza CN, calcolato sui 20.579 brevetti comuni: **0,646 per Qwen 4B**, **0,740 per SBERT-adapt-ub**, **0,876 per Pat-SPECTER**.

### Lettura prudente

- Tutti e tre i modelli mostrano associazione misurabile con le etichette WIPO, ma i valori AMI non sono validazione indipendente: le etichette derivano dal disegno del campione e dalla concordanza IPC–WIPO.
- SBERT ha la silhouette più alta nelle due coorti testate. Le geometrie degli embedding sono diverse, quindi il valore è descrittivo e non basta per decretare un modello vincitore.
- L'accordo tra partizioni dei modelli è moderato e varia per coppia. I modelli non producono semplicemente gli stessi cluster rinominati.
- Togliere CN cambia in misura diversa la partizione dei brevetti comuni. La maggiore stabilità full/no-CN di Pat-SPECTER in questo confronto è un risultato descrittivo del seed e del run specificati, non una proprietà universale del modello.
- L'AMI con l'ufficio nel corpus completo è 0,164 per Qwen 4B, contro 0,034 per SBERT e 0,043 per Pat-SPECTER; nella coorte senza CN scende rispettivamente a 0,037, 0,026 e 0,030. È un segnale da discutere come possibile associazione del clustering all'ufficio e alla composizione del corpus, non una misura di qualità tecnologica.
- K=16 è stato esaminato nel run, ma K=8 è il livello scelto per le card comparabili e la revisione umana. Non è stato dimostrato che K=8 sia un optimum o che esista un unico K corretto.

Fonte numerica: [`analysis/results/run_20261118T132255Z/metrics/model_k_summary.csv`](../analysis/results/run_20261118T132255Z/metrics/model_k_summary.csv), [`cross_model_ari_reference_seed.csv`](../analysis/results/run_20261118T132255Z/metrics/cross_model_ari_reference_seed.csv) e [`full_vs_no_cn_refit_ari.csv`](../analysis/results/run_20261118T132255Z/metrics/full_vs_no_cn_refit_ari.csv). La [pagina comparativa locale](model-comparison.html) mostra le card per i tre modelli e le due coorti.

## 5. Cosa possiamo sostenere adesso

Una formulazione sostenibile è che, in un corpus bilanciato per selezione WIPO e sbilanciato per ufficio, embedding diversi producono partizioni con associazione misurabile alla struttura WIPO, ma con profili e assegnazioni non identici. Le card rendono visibile la coerenza lessicale e classificatoria dei cluster e i brevetti ambigui o periferici. I risultati sono sensibili al modello, a K e alla composizione della coorte.

Non abbiamo ancora dimostrato che:

- i cluster rappresentino una tassonomia tecnologica unica o “vera”;
- un modello sia globalmente superiore sulla base della silhouette o dell'AMI;
- il campione sia rappresentativo dell'intera popolazione mondiale dei brevetti;
- il campione sia più eterogeneo di un altro senza un confronto costruito sullo stesso protocollo;
- le card equivalgano a una valutazione esperta e indipendente della qualità semantica.

## 6. Priorità prima della stesura

1. **Revisione umana mirata:** leggere le otto card Qwen K=8 (termini, WIPO, IPC e cinque brevetti centrali), annotare coerenza, sovrapposizioni e casi di confine; poi confrontare le differenze più informative con SBERT e Pat-SPECTER.
2. **Congelare la tabella principale:** decidere se il paper usa come riferimento il WIPO di selezione, il WIPO IPC-compatibile primario o soprattutto i profili multi-label; mantenere chiara la distinzione.
3. **Verificare la sensibilità geografica:** descrivere full vs senza CN come refit su coorti diverse e leggere i risultati insieme a uffici, kind code e distribuzione WIPO. Evitare di chiamarlo un effetto causale della Cina.
4. **Usare K=16 come sensibilità**, non aggiungere ogni variante alla narrativa centrale. Riportare i risultati che cambiano l'interpretazione.
5. **Controllare tracciabilità e citazioni:** conservare la configurazione del run, le revisioni dei modelli, la versione della concordanza WIPO e le fonti dei dati; separare risultati del run corrente da analisi precedenti del Patent Observatory.

## 7. Mappa delle fonti nella repo

- [Guida ai documenti](README.md)
- [Protocollo e output della pipeline](../analysis/README.md)
- [Configurazione del run corrente](../analysis/results/run_20261118T132255Z/run_config.json)
- [Risultati e audit del run](../analysis/results/run_20261118T132255Z/)
- [Patent Observatory di Brian](patent-observatory/README.md) — dashboard più ampia e risultati di notebook precedenti; non va confusa con la pagina comparativa a tre modelli.

