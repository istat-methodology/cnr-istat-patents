# Revisione manuale delle label dei cluster

Nota di lavoro per la revisione interpretativa dei cluster K=8 del run `run_20261118T132255Z`. È distinta dal Patent Observatory di Brian. Le label sono proposte descrittive, non una tassonomia tecnologica validata. I commenti motivano la lettura usando i termini c-TF-IDF, i brevetti centrali e i profili WIPO già presenti nel run; non sono state rilanciate analisi.

## Qwen3-Embedding-4B — corpus completo, K=8

| Cluster | Label di lavoro | Commento motivazionale |
|---|---|---|
| 0 | Biotecnologie e terapie biologiche | I termini su proteine, anticorpi e cancro sono coerenti con esempi su anticorpi, polipeptidi e composti terapeutici. Anche i campi WIPO prevalenti — farmaceutica e biotecnologie — sostengono la label. |
| 1 | Macchinari e attrezzature per processi industriali *(provvisoria)* | Gli esempi centrali riguardano macchine per centrare, trasportare, pompare o lavorare materiali; la scheda include però anche forni, valvole e impianti per acque reflue. La varietà dei campi WIPO e la quota CN del 98,9% invitano a mantenere la label cauta. |
| 2 | Dispositivi semiconduttori e optoelettronici | Gli esempi centrali includono dispositivi per semiconduttori, sensori ottici, transistor a film sottile e substrati piezoelettrici. Semiconduttori e ottica sono anche i campi WIPO più compatibili. |
| 3 | Materiali e processi chimici | I brevetti centrali trattano la preparazione di nanomateriali, silice, polimeri e altri composti. La distribuzione WIPO è articolata, ma si concentra su polimeri, materiali e chimica di base. |
| 4 | Elettronica per il rilevamento e l’elaborazione dei segnali | Gli esempi vanno da circuiti e sensori a metodi di elaborazione dei segnali. La label descrive questo nucleo, mentre i casi periferici mostrano che il cluster comprende anche applicazioni meno omogenee. |
| 5 | Comunicazione digitale: protocolli, servizi e apparati | I brevetti centrali riguardano metodi e apparati di comunicazione, richieste di rete, servizi e gestione dei dati. La presenza di dispositivi accanto a protocolli e servizi motiva la label estesa. |
| 6 | Applicazioni biotecnologiche in ambito medico e agroalimentare | Gli esempi spaziano dalla diagnostica e dai dispositivi per la selezione degli spermatozoi a polisaccaridi di origine naturale e metodi di estrazione vegetale. I campi WIPO comprendono biotecnologie, tecnologie mediche, chimica alimentare e farmaceutica; il 95,3% dei brevetti è CN. |
| 7 | Sistemi di propulsione e controllo dei veicoli | Gli esempi centrali comprendono motori e trasmissioni per veicoli, insieme a sistemi di controllo dell’aria e delle ventole. La prevalenza WIPO di Trasporti e Motori, pompe e turbine sostiene questa lettura. |

La label del cluster 1 resta provvisoria. Le quote WIPO compatibili sono multi-label e non rappresentano classi esclusive.

## Fonti locali

- Schede cluster: [`full__qwen3-embedding-4b__k8__cluster_cards.csv`](../analysis/results/run_20261118T132255Z/profiles/full__qwen3-embedding-4b__k8__cluster_cards.csv)
- Esempi di brevetti: [`full__qwen3-embedding-4b__k8__patent_examples.csv`](../analysis/results/run_20261118T132255Z/profiles/full__qwen3-embedding-4b__k8__patent_examples.csv)

## SBERT-adapt-ub — corpus completo, K=8

| Cluster | Label di lavoro | Commento motivazionale |
|---|---|---|
| 0 | Materiali funzionali e metodi di sintesi | Gli esempi centrali comprendono ossido di ittrio, zeoliti, compositi per il trattamento dell’acqua, trattamenti superficiali dei metalli e materiali compositi conduttivi. La prevalenza WIPO di polimeri, materiali e chimica di base sostiene la lettura come cluster di materiali e relative preparazioni. |
| 1 | Sistemi termici e trattamento di aria e acque | Caldaie, gas di scarico, calore residuo e acque reflue ricorrono nei termini; gli esempi centrali includono filtri per emissioni industriali, dispositivi per condensatori e compressori, cappe aspiranti e regolazione termica. I campi WIPO prevalenti sono processi termici, tecnologie ambientali e ingegneria chimica. |
| 2 | Sensori d’immagine e dispositivi optoelettronici | I cinque esempi centrali riguardano sensori d’immagine, dispositivi di acquisizione e fotodetettori con pixel e componenti semiconduttori. La quasi pari compatibilità WIPO con ottica e semiconduttori è coerente con la label. |
| 3 | Macchinari per la lavorazione dei materiali | Gli esempi vanno dalla rimozione degli scarti e dal taglio di alimenti alla scanalatura di lastre, alla produzione di packaging plastico e alla setacciatura della pasta di carta. I campi WIPO sono distribuiti tra macchine utensili, macchine tessili e cartarie e altre macchine speciali; l’88% dei brevetti è CN. |
| 4 | Software e strumenti di comunicazione | Gli esempi centrali riguardano interfacce di controllo IoT, analisi di dati da sensori, diagnosi di guasti di rete, gestione dello spettro radio e rilevamento di anomalie in reti connesse. Informatica, comunicazione digitale e metodi IT per la gestione sono i campi WIPO più compatibili. |
| 5 | Farmaci e terapie biotecnologiche | Gli esempi comprendono coniugati anticorpo-farmaco, composti che degradano proteine bersaglio, composizioni immunogeniche, nanobodies e una formulazione di medicina tradizionale cinese. I campi WIPO prevalenti sono prodotti farmaceutici e biotecnologie. |
| 6 | Circuiti elettronici per comunicazione e acquisizione dei segnali | I termini ricorrenti indicano circuiti, transistor, amplificatori e segnali. Gli esempi centrali riguardano attenuatori programmabili, rilevamento e acquisizione di segnali, adattamento d’impedenza per la comunicazione wireless e regolazione della gamma di un convertitore analogico-digitale. I campi WIPO più compatibili sono processi di comunicazione di base, apparecchiature elettriche e telecomunicazioni. |
| 7 | Meccanismi e componenti per il trasporto e la movimentazione | Gli esempi centrali comprendono una cerniera per braccio, un meccanismo per canne fumarie, dispositivi di serraggio e posizionamento e un ausilio di sicurezza. I termini e i campi WIPO richiamano trasporti, elementi meccanici e movimentazione; il cluster resta eterogeneo e il 79,6% dei brevetti è CN. |

Le quote WIPO compatibili sono multi-label e non rappresentano classi esclusive. Le label e i commenti sono descrittivi e restano soggetti alla revisione dei brevetti centrali e periferici.

### Fonti locali

- Schede cluster: [`full__sbert-adapt-ub__k8__cluster_cards.csv`](../analysis/results/run_20261118T132255Z/profiles/full__sbert-adapt-ub__k8__cluster_cards.csv)
- Esempi di brevetti: [`full__sbert-adapt-ub__k8__patent_examples.csv`](../analysis/results/run_20261118T132255Z/profiles/full__sbert-adapt-ub__k8__patent_examples.csv)
