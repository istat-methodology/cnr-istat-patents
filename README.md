# cnr-istat-patents

A sample of patent publications, balanced across technology fields, and a set of notebooks to explore it.
The repository is meant for students: read the data, build one merged dataset, and analyse the content of patent titles and abstracts.

## The data in one minute

- **64,000 rows**, 63,968 distinct patent publications, published between January 2021 and September 2026.
- Selected from Google Patents Public Datasets (BigQuery), with **2,000 publications for each of 32 WIPO technology fields**.
- WIPO groups IPC codes into 35 technology fields. We cover fields **1 to 32** (four sectors: Electrical engineering, Instruments, Chemistry, Mechanical engineering).
  Fields **33–35** ("Other fields": Furniture and games, Other consumer goods, Civil engineering) are **not** included.
- For each publication we have the English title and abstract, the publication date and all IPC codes.
- The selection is balanced by field, not by country. It cannot be used to estimate how frequent a technology is among all patents.

Details are in [`docs/methodology.md`](docs/methodology.md).

## How the data were extracted

The data were extracted with **Google BigQuery**, using the web console of Google Cloud (BigQuery Studio, in the browser).
The patents are in a public table, `patents-public-data.patents.publications`, that anyone with a Google Cloud project can query.

The four SQL files in `queries/` were pasted into the query editor and run there (one per WIPO sector).
The result of each query was exported as a CSV file and saved in `data/raw/` with the same base name as the query.
No programming environment was needed for this step.

You do **not** need a Google Cloud account to use this repository: the raw results are already in `data/raw/`.
If you want to reproduce or change an extraction, open a query, check the estimated amount of data processed (shown by the console before you run it),
and run it from your own project. Queries are billed to the project that runs them, so check the free tier first.
Details of the query logic are in [`docs/methodology.md`](docs/methodology.md), and the step-by-step description is in [`docs/workflow.md`](docs/workflow.md).

## Quick start

You need Python 3.10 or newer.

```
git clone git@github.com:istat-methodology/cnr-istat-patents.git
cd cnr-istat-patents

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd notebooks
jupyter lab
```

Open the notebooks in order. They use relative paths, so start Jupyter from the `notebooks/` folder.

## Notebooks

| # | Notebook | What you do |
|---|---|---|
| 00 | `00_overview` | Learn the concepts (patent, IPC, WIPO field), look at one patent, check the setup |
| 01 | `01_read_raw_data` | Read the four raw CSV files and check them |
| 02 | `02_merge_and_clean` | Merge the files, clean the text, save two merged datasets |
| 03 | `03_eda_structure` | Fields, years, patent offices, document types |
| 04 | `04_eda_text` | Length and quality of text, vocabulary, words per field, similarity between fields |
| 05 | `05_eda_ipc_and_overlap` | IPC codes with their titles; how many patents belong to more than one field |

Notebooks 03–05 only need the Parquet files that notebook 02 writes in `data/processed/`. If you only want to explore, they are already in the repository.

## Repository structure

```
README.md
requirements.txt
docs/
  methodology.md        how the corpus was designed and extracted
  workflow.md           the steps from the WIPO rules to the notebooks
  data_dictionary.md    columns of every file, known problems
queries/                4 BigQuery SQL files (one per WIPO sector)
ipc/
  ipc_technology.xlsx   WIPO IPC-Technology concordance (March 2026)
  EN_ipc_scheme_20260101.xml   WIPO IPC scheme 2026.01
  ipc_titles.csv        titles of IPC symbols, built from the XML
src/
  build_ipc_titles.py   script that builds ipc_titles.csv
  parquet_to_csv.py     script that converts the merged Parquet files to CSV (optionally a random sample)
data/
  raw/                  the 4 CSV files exported from BigQuery
  processed/            merged datasets (Parquet)
notebooks/              notebooks 00-05
papers/                 background reading
```

## Data files

| File | Rows | Use |
|---|---:|---|
| `data/raw/patents_<sector>_2021-2026_n2000.csv` (4 files) | 64,000 in total | raw extraction, never modified |
| `data/processed/patents_2021-2026_by_field.parquet` | 64,000 | one row per (publication, field): compare fields |
| `data/processed/patents_2021-2026_by_publication.parquet` | 63,968 | one row per publication: count patents |

**Parquet.** The merged datasets are Parquet files, a compact table format that keeps column types and lists and is fast to read (`pd.read_parquet`).
The notebooks read them directly. You cannot open a Parquet file in Excel; if you want a CSV, or a CSV with a random sample, run

```
python src/parquet_to_csv.py                       # CSV of both files, next to the Parquet files
python src/parquet_to_csv.py --sample 5000         # a random sample of 5,000 rows
```

CSV files created in `data/processed/` are ignored by git.

## Things to keep in mind

- About two thirds of the publications come from China; sampling was not balanced by country.
- Applications, granted patents and utility models are mixed.
- Over half of the patents match the IPC rules of more than one field: field labels are not mutually exclusive.
- Some abstracts are placeholders or truncated. They are flagged, not removed.

See [`docs/data_dictionary.md`](docs/data_dictionary.md) for the full list.

## Sources

- WIPO IPC–Technology Concordance and IPC scheme: https://www.wipo.int/en/web/ip-statistics
- Google Patents Public Datasets: https://github.com/google/patents-public-data
- OECD (2025), *Identifying emerging AI technologies using patent data*, in `papers/`.
