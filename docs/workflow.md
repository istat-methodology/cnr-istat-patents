# Workflow

From the WIPO concordance to the analysis notebooks.

```
ipc/ipc_technology.xlsx          WIPO rules: IPC pattern -> technology field
        |
        v
queries/*.sql                    4 BigQuery queries, one per WIPO sector
        |  run in BigQuery, export as CSV
        v
data/raw/*.csv                   4 raw files, 64,000 rows (one row = publication x field)
        |  notebooks 01 and 02
        v
data/processed/                  merged and cleaned files (Parquet)
        |  notebooks 03, 04, 05
        v
exploratory analysis             structure, text, IPC codes and overlap

ipc/EN_ipc_scheme_20260101.xml --(src/build_ipc_titles.py)--> ipc/ipc_titles.csv
                                  titles of IPC codes, used in notebooks 00 and 05
```

## Step 1. Rules (already done)

The WIPO concordance gives, for each technology field, a list of IPC patterns. See `docs/methodology.md`, section 4, for how the Excel rules were turned into SQL.

## Step 2. Extraction (already done)

The extraction was done in the Google Cloud console, with BigQuery (BigQuery Studio, in the browser). No local code is involved.

1. In the Google Cloud console, open BigQuery and create a new query. Paste the content of one file from `queries/` (GoogleSQL).
2. Check the estimated bytes processed, shown by the editor before you run. Public tables are large and the query reads them in full. The query runs on your own project, so it is billed there.
3. Run the query and export the result as CSV (the results panel has a "Save results" menu).
4. Save it in `data/raw/` with the same base name as the query. The name must follow the schema in `docs/methodology.md`, section 8.

Students do not need a Google Cloud account to work with the notebooks: the CSV files are in the repository.

## Step 3. IPC titles (already done)

```
python src/build_ipc_titles.py
```

This reads `ipc/EN_ipc_scheme_20260101.xml` and writes `ipc/ipc_titles.csv`. Run it again only if you change the IPC edition. The script is documented in its first lines.

## Step 4. Notebooks

Run the notebooks in order. Each one starts with a short description of what it needs and what it produces.

| Notebook | What it does | Reads | Writes |
|---|---|---|---|
| `00_overview` | Concepts (IPC, WIPO field, sector), a first look at one patent, check of the setup | `data/raw/`, `ipc/` | nothing |
| `01_read_raw_data` | Read the four CSV files, check columns, types, missing values and duplicates | `data/raw/` | nothing |
| `02_merge_and_clean` | Merge the four files, clean the text, add helper columns, save two merged files | `data/raw/` | `data/processed/` |
| `03_eda_structure` | Fields and sectors, years, patent offices, document types | `data/processed/` | nothing |
| `04_eda_text` | Title and abstract length, vocabulary, text quality, duplicates, similarity between fields | `data/processed/` | nothing |
| `05_eda_ipc_and_overlap` | IPC codes and their titles, and how many patents also match other fields | `data/processed/`, `ipc/` | nothing |

Notebooks 03 to 05 only need the files written by notebook 02.

## Step 5. Merged files

Notebook 02 writes the same content in two shapes, as Parquet files:

| File | One row is | Rows |
|---|---|---:|
| `patents_2021-2026_by_field` | a publication selected for a field | 64,000 |
| `patents_2021-2026_by_publication` | a distinct publication, with its fields in a list | 63,968 |

Use the *by field* file to compare fields, and the *by publication* file when you count patents.

**Why Parquet.** It is about 2.5 times smaller than CSV, keeps column types and lists, and reads much faster. Only Parquet files are kept in the repository, which keeps it small. The notebooks read them with `pd.read_parquet`.

**From Parquet to CSV.** A Parquet file cannot be opened in Excel. To create a CSV, or a CSV with a random sample, use the script `src/parquet_to_csv.py` from the repository root:

```
python src/parquet_to_csv.py                          # both files, all rows
python src/parquet_to_csv.py --sample 5000 --seed 42 --out-dir data/samples
```

In the CSV, dates are written as `YYYY-MM-DD` and list columns become text separated by `;`. CSV files in `data/processed/` and in `data/samples/` are ignored by git.

## Set-up

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

Open the notebooks from the `notebooks/` folder. They use relative paths (`../data/...`), so the notebook folder must be the working folder.

## Reproducibility

- The SQL files and the sampling seed (`wipo-pilot-v1`) define the extraction. The CSV files in `data/raw/` are the frozen result: if the Google table is updated, a new run can give a different sample.
- Notebook 02 is deterministic. Running it again rebuilds the merged files from the raw files.
- Keep the same file names when you add new extractions, and update `docs/methodology.md`.

## Planned for later

- Text embeddings of titles and abstracts, to test whether text recovers the technology structure. This needs a GPU, for example on Azure.
- Identification of AI-related patents, using the OECD method in `papers/` as a starting point.
- Extraction of fields 33 to 35, if needed.
