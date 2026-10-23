# Data dictionary

Columns of every file in the repository, and known problems in the data.

## 1. Raw files: `data/raw/patents_<sector>_2021-2026_n2000.csv`

Exactly as exported from BigQuery. One row is one publication **selected for one WIPO field**. Four files, 64,000 rows in total.

| Column | Type | Meaning |
|---|---|---|
| `wipo_field_number` | integer | WIPO field for which the publication was selected (1–32) |
| `wipo_field_name` | text | Name of that field |
| `wipo_sector` | text | Sector of that field: Electrical engineering, Instruments, Chemistry, Mechanical engineering |
| `publication_number` | text | Office, number and kind code, for example `US-2022000739-A1` |
| `publication_date` | integer `YYYYMMDD` | Publication date |
| `title_en` | text | An English title, as in the source |
| `abstract_en` | text | An English abstract, as in the source (can contain line breaks) |
| `ipc_codes` | text | All IPC codes of the publication, separated by `;`, for example `G06N3/08;G06N3/04` |

## 2. Merged files: `data/processed/`

Created by notebook `02_merge_and_clean`. Two tables with 24 columns each, saved as **Parquet** files.

- `patents_2021-2026_by_field`: one row per (publication, field). 64,000 rows.
- `patents_2021-2026_by_publication`: one row per distinct publication. 63,968 rows.

In **Parquet** the columns marked *list* are real lists. If you create a CSV with `src/parquet_to_csv.py` (see section 2b), they become text with items separated by `;`, and dates are written as `YYYY-MM-DD`.
The text is the **cleaned** text (HTML entities decoded, whitespace collapsed). The original text is in `data/raw/`.

| Column | In by_field | In by_publication | Type | Meaning |
|---|:-:|:-:|---|---|
| `wipo_sector` | yes | no | text | Sector of the selection field |
| `wipo_field_number` | yes | no | integer | Selection field (1–32) |
| `wipo_field_name` | yes | no | text | Name of the selection field |
| `wipo_field_numbers` | no | yes | list of integers | Fields for which the publication was selected (one, rarely two) |
| `wipo_field_names` | no | yes | list of text | Names of those fields |
| `wipo_sectors` | no | yes | list of text | Sectors of those fields |
| `publication_number` | yes | yes | text | Publication identifier |
| `office` | yes | yes | text | First part of the publication number (`CN`, `US`, `WO`, `EP`...) |
| `kind_code` | yes | yes | text | Last part of the publication number (`A`, `A1`, `B2`, `U`...). Meaning depends on the office |
| `publication_date` | yes | yes | date | Publication date |
| `publication_year` | yes | yes | integer | Year of `publication_date` |
| `publication_month` | yes | yes | integer | Month of `publication_date` |
| `title_clean` | yes | yes | text | Title, cleaned |
| `abstract_clean` | yes | yes | text | Abstract, cleaned |
| `title_n_words` | yes | yes | integer | Words in the title |
| `abstract_n_chars` | yes | yes | integer | Characters in the abstract |
| `abstract_n_words` | yes | yes | integer | Words in the abstract |
| `abstract_is_placeholder` | yes | yes | boolean | Abstract with no information: empty, `(無)`, "Information on abstract not available", a copyright line, or fewer than 30 characters |
| `abstract_is_short` | yes | yes | boolean | Fewer than 100 characters. A warning: includes truncated and complete short abstracts |
| `abstract_has_cjk` | yes | yes | boolean | The "English" abstract contains Chinese, Japanese or Korean characters |
| `title_is_duplicate` | yes | yes | boolean | Same title (ignoring case) as another publication |
| `abstract_is_duplicate` | yes | yes | boolean | Same abstract (ignoring case) as another publication |
| `ipc_codes` | yes | yes | text | All IPC codes, separated by `;`, in alphabetical order (the order is **not** a ranking: the first code is not the main one) |
| `n_ipc` | yes | yes | integer | Number of IPC codes |
| `ipc_subclasses` | yes | yes | list of text | Distinct subclasses (first 4 characters of each code), sorted |
| `n_subclasses` | yes | yes | integer | Number of distinct subclasses |
| `n_fields` | yes | yes | integer | In how many fields the publication was selected (1 or 2) |

Reading the files:

```python
import pandas as pd
df = pd.read_parquet("data/processed/patents_2021-2026_by_field.parquet")
```

## 2b. What is Parquet, and how to get a CSV

Parquet is a file format for tables. Compared with CSV it is about 2.5 times smaller (31 MB instead of 77 MB here), it keeps the type of each column (dates, integers, booleans), it can store lists, and it is much faster to read.
It is a binary format: it cannot be opened in Excel or in a text editor. Pandas reads it with `pd.read_parquet` (the `pyarrow` package, in `requirements.txt`, does the work).

To get a CSV, or a CSV with a random sample, use `src/parquet_to_csv.py` from the repository root:

```
python src/parquet_to_csv.py                                  # both files, all rows
python src/parquet_to_csv.py --sample 5000 --seed 42 --out-dir data/samples
```

In the CSV, dates are written as `YYYY-MM-DD` and the list columns (`ipc_subclasses`, `wipo_field_numbers`, `wipo_field_names`, `wipo_sectors`) are text with items separated by `;`.
Split them with `.str.split(";")` after reading. In the `by_publication` CSV, `wipo_field_numbers` is a number for publications with one field (`16`) and text for two (`16;18`).
CSV files in `data/processed/` and `data/samples/` are ignored by git. From pandas you can also write one directly with `df.to_csv("file.csv", index=False)`.

## 3. IPC titles: `ipc/ipc_titles.csv`

Created by `src/build_ipc_titles.py` from the WIPO IPC scheme 2026.01. One row per IPC symbol (80,146 rows).

| Column | Meaning |
|---|---|
| `symbol` | IPC symbol in the same format as the patent data: `A`, `A01`, `A01B`, `G06N3/00`, `G06N3/08` |
| `level` | `section`, `class`, `subclass`, `main_group` or `subgroup` |
| `title` | Official English title. Sections, classes and subclasses are in capitals. Several title parts are joined by `; ` |
| `short_title` | First title part, in sentence case when the title is mostly in capitals. Use it for labels |
| `full_title` | For main groups and subgroups: the chain of titles from the main group down, joined by ` > `. Subgroup titles are often fragments, so read them with their parents |
| `depth` | 0 section, 2 class, 4 subclass, 5 main group; for subgroups the number of dots in the scheme (1–9) |
| `parent` | Symbol of the parent entry |
| `source` | `scheme_2026.01`, or `hardcoded` for the one row added by hand (`H01L`) |

Subclass `H01L` is missing from IPC 2026.01 (moved to `H10`) but still used in the patent data. See `docs/methodology.md`, section 9.

## 4. WIPO concordance: `ipc/ipc_technology.xlsx`

Sheet `IPC Tech Concordance`. The header is in row 7. Columns used: `Field_number`, `Sector_en`, `Field_en`, `IPC_code` (one rule per row; `%` means "any ending").
There are also French and Spanish names, an update date and a remark column.

## 5. Known problems

Counts refer to the current files and are measured by the notebooks.

| Issue | Where it shows | What to do |
|---|---|---|
| Strong geographic imbalance (China has about two thirds of the publications) | `office` | Check results by office, or restrict to one office |
| Mixed document types; kind codes differ by office | `kind_code` | Do not compare "granted" and "applications" across offices without care |
| Utility models (kind code starting with `U`), almost all Chinese | `kind_code` | Consider excluding them for text comparisons |
| The same invention in several publications; near-duplicates are not flagged | `abstract_is_duplicate` flags only exact copies | Group by family before train/test splits |
| A publication can fit several fields; more than half match two or more | notebook 05 | Treat field labels as non-exclusive |
| Placeholder, truncated or very short abstracts | `abstract_is_placeholder`, `abstract_is_short` | Filter or inspect |
| OCR noise (page numbers, figure labels) in a few abstracts | not flagged | Inspect long abstracts |
| English text in a few abstracts is actually CJK | `abstract_has_cjk` | Filter |
| "English" text may be a translation | — | Do not assume original language |
| 2026 is incomplete (latest date 17 September 2026) | `publication_year` | Do not compare 2026 with full years |
| Fields 33–35 are not in the corpus | — | Conclusions apply to fields 1–32 |
| IPC titles are missing for `H01L` groups and for some codes deleted from IPC after publication | `ipc/ipc_titles.csv` | Use subclass titles |
