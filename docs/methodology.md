# Methodology

How the patent corpus was designed and extracted.
Status: working version, October 2026.

## 1. Aim

We build an exploratory corpus of patent publications, balanced across technology fields, to study the content of patent titles and abstracts. The corpus is meant for comparing technologies with each other.

The selection is based on the International Patent Classification (IPC) and on the WIPO concordance between IPC codes and technology fields. We do not apply any keyword filter, and the corpus is not restricted to a single technology such as AI.

Equal quotas per field do not reproduce the real distribution of patenting. The corpus cannot be used, on its own, to estimate how frequent a technology is in the population of patents.

## 2. Scope at a glance

| Parameter | Choice |
|---|---|
| Source | Google Patents Public Datasets, via BigQuery |
| Table | `patents-public-data.patents.publications` |
| Classification | WIPO IPC–Technology Concordance, update March 2026 |
| Fields included | WIPO fields 1 to 32 |
| Fields excluded | 33 Furniture, games; 34 Other consumer goods; 35 Civil engineering |
| Period | Publication date from 1 January 2021 to 30 September 2026, both included |
| Language | English title and English abstract available and not empty |
| Quota | Up to 2,000 publications per WIPO field |
| Geography | No filter on patent office |
| Legal status | No filter (applications and granted patents are both included) |
| Result | 64,000 rows, 63,968 distinct publications |

Notes on these choices:

- The period is an operational choice of about five years and nine months. It includes the pandemic years and is not a formal definition of "post-COVID".
- English text does not prove that English is the language of the original filing.
- In the delivered files the latest publication date is 17 September 2026, not 30 September.

## 3. WIPO technology fields

WIPO groups IPC symbols into **35 technology fields**, which are grouped into **5 sectors**. The 35 fields are not 35 IPC codes: each field is defined by a list of IPC rules.

| Sector | # | Technology field |
|---|---:|---|
| Electrical engineering | 1 | Electrical machinery, apparatus, energy |
| | 2 | Audio-visual technology |
| | 3 | Telecommunications |
| | 4 | Digital communication |
| | 5 | Basic communication processes |
| | 6 | Computer technology |
| | 7 | IT methods for management |
| | 8 | Semiconductors |
| Instruments | 9 | Optics |
| | 10 | Measurement |
| | 11 | Analysis of biological materials |
| | 12 | Control |
| | 13 | Medical technology |
| Chemistry | 14 | Organic fine chemistry |
| | 15 | Biotechnology |
| | 16 | Pharmaceuticals |
| | 17 | Macromolecular chemistry, polymers |
| | 18 | Food chemistry |
| | 19 | Basic materials chemistry |
| | 20 | Materials, metallurgy |
| | 21 | Surface technology, coating |
| | 22 | Micro-structural and nano-technology |
| | 23 | Chemical engineering |
| | 24 | Environmental technology |
| Mechanical engineering | 25 | Handling |
| | 26 | Machine tools |
| | 27 | Engines, pumps, turbines |
| | 28 | Textile and paper machines |
| | 29 | Other special machines |
| | 30 | Thermal processes and apparatus |
| | 31 | Mechanical elements |
| | 32 | Transport |
| **Other fields (not in the corpus)** | 33 | Furniture, games |
| | 34 | Other consumer goods |
| | 35 | Civil engineering |

**The corpus covers fields 1 to 32 only.** The "Other fields" sector (33–35) was excluded on purpose, so the four sectors in the data are Electrical engineering, Instruments, Chemistry and Mechanical engineering. Anything we say about "technology in general" is therefore limited to these 32 fields.

The WIPO fields cut across the IPC sections (A to H). For example, *Computer technology* is mostly built from codes in section G (Physics), *Digital communication* from section H (Electricity), and *Environmental technology* from sections A, B, C, E, F and G.

## 4. From the WIPO Excel file to the SQL queries

The starting point is the file `ipc/ipc_technology.xlsx` (sheet `IPC Tech Concordance`, last update March 2026), published by WIPO. Each row is one rule that links an IPC pattern to a field.

The columns we use are `Field_number`, `Sector_en`, `Field_en` and `IPC_code`. The sheet has 771 rules for the 35 fields. For fields 1 to 32 there are **667 rules**.

How to read a rule:

- `%` means "any suffix". `G06Q%` matches every code that starts with `G06Q`.
- Some rules go down to the group level, for example `H04N21/%`. That detail must be kept: `H04N21/%` belongs to *Digital communication* while other `H04N` groups belong to *Audio-visual technology* or *Telecommunications*.
- The rules of one field are alternatives. A publication matches the field if **at least one** of its IPC codes matches **at least one** rule of the field.

How the queries were built from the sheet:

1. The rules of each field were taken from the sheet and written as a list of patterns (`'G06C%'`, `'G06D%'`, ...). Spaces inside the sheet codes are removed (`H04N  21/%` becomes `H04N21/%`) and letters are upper case.
2. One query template is shared by all queries. Only the list of fields, with their number, name and rules, changes.
3. We wrote one query per WIPO sector (4 files in `queries/`) instead of one per field.
4. The rules in the four SQL files were compared with the Excel sheet: for each of the 32 fields the two sets of rules are identical.

The broad prefixes sometimes used in introductory material (for example "Computer technology = G06") are not used. The full concordance is the reference, because IPC is revised over time.

## 5. Eligibility rule

A publication is eligible for a field if:

1. its publication date is between 2021-01-01 and 2026-09-30;
2. it has a non-empty English title and a non-empty English abstract;
3. at least one of its IPC codes matches at least one rule of the field.

Before the comparison, IPC codes are upper-cased and spaces are removed. The check is written as an `EXISTS` condition, so a publication with several matching codes still produces one row per field.

## 6. Sampling inside each field

The quota of 2,000 is per WIPO field, not per IPC rule. A field with many rules does not get a larger quota.

Selection is pseudo-random and reproducible:

1. For each field, eligible publications are ordered by `FARM_FINGERPRINT` of the text `wipo-pilot-v1|<field number>|<publication number>`.
2. Ties are broken by publication number.
3. The first 2,000 are kept.

The seed text is `wipo-pilot-v1`. It was kept unchanged in all four queries.

A plain `LIMIT 2000` would not be random. A deterministic hash makes the selection repeatable with the same data, query and seed. If Google updates the public table, the sample can change, so the extracted identifiers must be kept (the CSV files in `data/raw/` serve this purpose).

If a field had fewer than 2,000 eligible publications, all of them would be kept. This did not happen: every field reached 2,000.

Not applied in this version: quotas by year, office or single IPC code; deduplication across fields; deduplication by patent family.

## 7. What each query returns

| Column | Content |
|---|---|
| `wipo_field_number` | Field for which the publication was selected |
| `wipo_field_name` | Name of that field |
| `wipo_sector` | Sector of that field |
| `publication_number` | Publication identifier, for example `US-2022000739-A1` |
| `publication_date` | Publication date, `YYYYMMDD` |
| `title_en` | One English title |
| `abstract_en` | One English abstract |
| `ipc_codes` | All IPC codes of the publication, separated by `;` |

If a publication has several English titles or abstracts, the query takes the first one in alphabetical order. All IPC codes are kept, not only those that made the publication eligible.

The field of selection is not necessarily the only field a patent could belong to. Notebook `05_eda_ipc_and_overlap` measures this.

## 8. File naming

Each query and the CSV it produces have the same base name; only the extension changes.

Schema: `patents_<sector>_2021-2026_n2000`

| Sector | Query | Dataset |
|---|---|---|
| Electrical engineering | `queries/patents_electrical_engineering_2021-2026_n2000.sql` | `data/raw/patents_electrical_engineering_2021-2026_n2000.csv` |
| Instruments | `queries/patents_instruments_2021-2026_n2000.sql` | `data/raw/patents_instruments_2021-2026_n2000.csv` |
| Chemistry | `queries/patents_chemistry_2021-2026_n2000.sql` | `data/raw/patents_chemistry_2021-2026_n2000.csv` |
| Mechanical engineering | `queries/patents_mechanical_engineering_2021-2026_n2000.sql` | `data/raw/patents_mechanical_engineering_2021-2026_n2000.csv` |

Rules:

- Lower case letters and underscores, no spaces.
- `n2000` means up to 2,000 publications **per WIPO field**, not per sector.
- `2021-2026` is the publication period, 1 January 2021 to 30 September 2026. The exact dates are in the header of each SQL file.
- Test runs with a quota of 10 per field use `n10` in both the query and the CSV name.
- The merged files in `data/processed/` follow the same logic: `patents_2021-2026_by_field.parquet` and `patents_2021-2026_by_publication.parquet`.

## 9. IPC code titles

The patent files contain IPC codes but not their meaning. To read results, we also use the official English titles of IPC symbols:

- Source: IPC scheme 2026.01 (XML master file) from WIPO, saved as `ipc/EN_ipc_scheme_20260101.xml`.
- The script `src/build_ipc_titles.py` flattens it into `ipc/ipc_titles.csv` (one row per symbol: section, class, subclass, main group, subgroup).
- The scheme 2026.01 no longer contains subclass `H01L` (its content moved to `H10` in 2023), but the concordance and the patent data still use it. The script adds one hardcoded title for `H01L`. Group titles for `H01L` (for example `H01L21/52`) are not available.
- About 1.4% of the codes with a group in the corpus have no title, mostly `H01L` groups and old codes deleted from the scheme.

Subclass titles (4 characters, such as `G06N`) are the most useful level for reading results. See `docs/data_dictionary.md` for the columns.

## 10. Known limitations

- **Geography.** Sampling is balanced by field, not by office. Chinese publications are about two thirds of the corpus.
- **Document types.** Applications, granted patents and utility models are mixed. Kind codes are not comparable across offices.
- **Families.** The same invention can appear as several publications (for example US and EP). No deduplication by family was done.
- **Overlap across fields.** A publication is selected for one field but may match the rules of others. Only 32 publications were selected for two fields, but when the WIPO rules are applied to every publication, more than half match two or more of the 32 fields (notebook `05_eda_ipc_and_overlap`). Field labels are therefore not mutually exclusive.
- **Text quality.** Some abstracts are placeholders, truncated or contain OCR noise. Some titles contain HTML entities. Notebook 02 flags and cleans these cases and keeps the original text.
- **Partial last year.** 2026 covers about nine months.
- **Fields 33 to 35** are not in the corpus.

## References

- WIPO, IP Statistics and IPC–Technology Concordance: https://www.wipo.int/en/web/ip-statistics
- WIPO IPC publication: https://ipcpub.wipo.int/
- WIPO IPC master files 2026.01: https://www.wipo.int/classifications/data/ipc/ITSupport_and_download_area/20260101/MasterFiles/
- Google Patents Public Datasets: https://github.com/google/patents-public-data
- Dataset schema: https://github.com/google/patents-public-data/blob/master/tables/dataset_Google%20Patents%20Public%20Datasets.md
- BigQuery cost control: https://docs.cloud.google.com/bigquery/docs/best-practices-costs
- OECD (2025), *Identifying emerging AI technologies using patent data*, in `papers/` (background reading for a later phase).
