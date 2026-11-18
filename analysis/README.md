# Analisi riproducibili dei brevetti WIPO32

Questa cartella contiene una pipeline Python da eseguire sul corpus completo e sugli embedding già calcolati. Non genera embedding, non modifica dati di input e non riesegue i notebook 13/14.

## Requisiti

Usa Python 3.10 o superiore. Nel virtualenv attivo, dalla radice della repository, installa le dipendenze dedicate:

```bash
python -m pip install -r analysis/requirements.txt
```

La pipeline usa NumPy, pandas, PyArrow, openpyxl, scikit-learn e threadpoolctl; non richiede CUDA né una GPU. `openpyxl` serve a leggere il file Excel della concordanza WIPO.

La macchina Azure mostrata ha già la struttura richiesta nella cartella `embeddings/` della repository:

```text
<cartella-embedding>/
  bge-m3/embeddings.npy
  bge-m3/ids.parquet
  qwen3-embedding-4b/embeddings.npy
  qwen3-embedding-4b/ids.parquet
  ...
```

Sono presenti gli otto modelli previsti; per ognuno, `ids.parquet` deve contenere `publication_number`. Lo script controlla gli identificativi, riallinea le righe all'ordine del corpus, verifica valori finiti e vettori non nulli, quindi ricalcola la normalizzazione L2 dopo la conversione da float16 a float32.

## Esecuzione consigliata su Azure

Dalla radice `~/projects/cnr-istat-patents` sulla macchina Azure:

```bash
python analysis/run_analysis.py \
  --data data/processed/patents_2021-2026_by_publication.parquet \
  --concordance ipc/ipc_technology.xlsx \
  --embeddings-dir embeddings \
  --output-dir ../patent-analysis-results
```

Per impostazione predefinita la pipeline:

- analizza tutti i brevetti e crea anche la coorte di sensibilità senza `office = CN`;
- usa gli otto modelli Hugging Face presenti nel dataset;
- stima K-means per `K = 8, 16`, con seed `42, 43, 44`, `n_init = 10`;
- calcola la silhouette coseno su un campione deterministico di 1.200 brevetti;
- salva le assegnazioni del seed 42, le metriche per seed, la stabilità tra seed, l'ARI tra modelli e l'ARI tra fit full/no-CN sui brevetti comuni.

I risultati vengono scritti in una nuova sottocartella con timestamp. L'output non va nella cartella Git della repository, così i file grandi e le tabelle derivate restano separati dai dati e dal codice sorgente.

### Riprendere un run interrotto

La pipeline può riprendere la cartella di un run già avviato. `--resume-dir` controlla la configurazione salvata, i checkpoint delle metriche, le assegnazioni e i profili. Salta le coppie modello/coorte complete, ricalcola dall'inizio un'eventuale coorte incompleta e, alla fine, produce tutti i riepiloghi nella cartella originale. Le impostazioni fondamentali e le versioni di NumPy, pandas e scikit-learn devono coincidere con quelle del run.

Per riprendere l'esecuzione mostrata nella sessione Azure, dalla radice `~/projects/cnr-istat-patents`:

```bash
python analysis/run_analysis.py \
  --data data/processed/patents_2021-2026_by_publication.parquet \
  --concordance ipc/ipc_technology.xlsx \
  --embeddings-dir embeddings \
  --output-dir ../patent-analysis-results \
  --resume-dir ../patent-analysis-results/run_20261118T132255Z
```

Non cambiare modelli, coorti, K, seed o parametri mentre riprendi. I modelli e le coorti già complete vengono conservati; se il run precedente si è fermato nel mezzo di una coorte, viene ripetuta soltanto quella coorte.

Per un run più breve, ad esempio su un solo modello:

```bash
python analysis/run_analysis.py \
  --data data/processed/patents_2021-2026_by_publication.parquet \
  --concordance ipc/ipc_technology.xlsx \
  --embeddings-dir embeddings \
  --output-dir ../patent-analysis-results \
  --models paecter \
  --cohorts full exclude-cn \
  --k 8 16 \
  --seeds 42 43 44
```

È possibile indicare un solo campione con `--cohorts full` oppure `--cohorts exclude-cn`. Per cambiare K, seed o dimensione del campione silhouette, usare `--k`, `--seeds` e `--silhouette-sample`.

## Cosa produce

La cartella del singolo run contiene:

- `audit/corpus_overview.csv`: conteggi di brevetti, codici IPC, field WIPO compatibili e quota CN;
- `audit/publication_wipo_matches.parquet`: field di selezione e tutti i field WIPO compatibili via IPC per pubblicazione;
- `audit/office_by_selection_field.csv`, `office_kind_code_by_selection_field.csv`, `office_by_ipc_compatible_field.csv` e `office_counts.csv`: composizione del corpus per ufficio, field e tipo documento;
- `audit/ipc_wipo_overlap_distribution.csv`: distribuzione del numero di field WIPO compatibili per brevetto;
- `metrics/seed_metrics.csv`, `model_k_summary.csv`, `seed_stability_ari.csv`: metriche, sintesi e stabilità;
- `metrics/cross_model_ari_reference_seed.csv`: somiglianza tra partizioni di modelli diversi sullo stesso corpus e K;
- `metrics/full_vs_no_cn_refit_ari.csv`: cambiamento delle assegnazioni sui brevetti comuni dopo il refit senza CN;
- `assignments/`: assegnazione per brevetto al seed di riferimento, incluse le liste di field WIPO selezionati e compatibili;
- `profiles/`: schede cluster, termini c-TF-IDF, composizione WIPO e brevetti centrali/periferici.

## Regole di interpretazione

- La composizione `ipc_compatible` usa **tutti** i field WIPO compatibili con i codici IPC di ciascun brevetto. Le quote possono quindi sommare a più del 100%: non sono classi esclusive.
- `selection_all` conserva i field usati per selezionare il brevetto nel corpus. Non è intercambiabile con la compatibilità IPC completa.
- Per il confronto con la convenzione storica a una label, `AMI_WIPO_compatible_primary` usa il field compatibile con numero più basso; `AMI_WIPO_selection_primary` usa analogamente il field di selezione più basso. Sono riferimenti convenzionali, non la “vera” area tecnologica né una validazione semantica.
- Le schede usano c-TF-IDF calcolato sui titoli e abstract aggregati per cluster. È un aiuto interpretativo; controllare i termini sui brevetti centrali e periferici.
- Il profilo per ufficio in ogni cluster riporta anche quota e lift rispetto alla coorte; aiuta a vedere se un cluster è concentrato su CN o su un altro ufficio.
- I brevetti centrali sono i più vicini al centroide K-means nella distanza euclidea usata dal fit. I casi `boundary` sono quelli con minor margine tra i due centroidi più vicini; non sono automaticamente errori.
- L'esclusione di CN identifica l'ufficio di pubblicazione nel prefisso del numero del brevetto. Non identifica paese di richiedente, inventore o priorità. Dato il peso di CN e la sua composizione diversa per field e `kind_code`, il fit senza CN è una coorte di sensibilità sostanziale.
- La silhouette viene stimata su un campione fisso per run; i valori tra modelli con geometrie diverse sono descrittivi. Non usare una singola metrica per stabilire un vincitore.
- Il corpus è bilanciato per field WIPO, non rappresentativo delle frequenze mondiali. Il 2026 è incompleto.

## Memoria, durata e interruzioni

È sufficiente una macchina CPU con memoria adeguata; come margine pratico, puntare a circa 16 GB di RAM. La matrice float32 più grande è circa 0,7 GB per modello, ma K-means e le conversioni richiedono ulteriore spazio temporaneo. I modelli vengono elaborati uno alla volta e il limite predefinito è quattro thread (`--threads`).

Il notebook 13 contiene un run full-corpus eseguito in precedenza: riporta all'incirca 7–31 minuti per modello sui nove modelli, circa due ore complessive nell'ambiente usato per quel run. È una stima indicativa; il doppio fit full/no-CN e la generazione dei profili aumentano la durata. La GPU non è usata dal codice.

La pipeline salva metriche progressivamente dopo ogni coorte completata. Se il processo si interrompe, i file già scritti restano disponibili e si può continuare con `--resume-dir`. Non eseguire due processi contemporaneamente sulla stessa cartella di run.
