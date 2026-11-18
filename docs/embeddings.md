# Embeddings

Embeddings of title + abstract for the 63,968 publications of `data/processed/patents_2021-2026_by_publication.parquet`, from 8 models.
They are published at https://huggingface.co/datasets/istat-ai/wipo32-patent-embeddings and are not in this repository (about 1 GB).
The script is `src/generate_embeddings.py`.

## What is embedded

- The text is the title followed by the abstract. For PAT-SPECTER it is `title [SEP] abstract`, the SPECTER convention. A missing title or abstract is an empty string.
- All publications are embedded, including the ones with a placeholder abstract. They are flagged in `ids.parquet` (`abstract_is_placeholder`).
- There is no chunking. A text longer than the maximum length of the model is truncated.
- The row order is the row order of the by-publication Parquet file. `ids.parquet` repeats it.

## Models

| Folder | Hugging Face model | Dim | Max length | Compute | Prefix | Truncated texts | Minutes |
|---|---|---:|---:|---|---|---:|---:|
| `bge-m3` | BAAI/bge-m3 | 1024 | 2048 | fp32 | none | 0 | 3.4 |
| `qwen3-embedding-4b` | Qwen/Qwen3-Embedding-4B | 2560 | 2048 | bf16 | instruction (below) | 0 | 17.5 |
| `qwen3-embedding-0.6b` | Qwen/Qwen3-Embedding-0.6B | 1024 | 2048 | bf16 | instruction (below) | 0 | 4.6 |
| `embeddinggemma-300m` | google/embeddinggemma-300m | 768 | 2048 | bf16 | `task: clustering \| query: ` | 0 | 2.0 |
| `paecter` | mpi-inno-comp/paecter | 1024 | 512 | fp32 | none | 20 | 3.0 |
| `pat-specter` | mpi-inno-comp/pat_specter | 768 | 512 | fp32 | none | 26 | 1.2 |
| `sbert-adapt-ub` | graziasveva93/sbert-adapt-ub | 384 | 512 | fp32 | none | 31 | 0.6 |
| `mpnet` | sentence-transformers/all-mpnet-base-v2 | 768 | 384 | fp32 | none | 199 | 1.7 |

Qwen instruction, written for this project and added in front of every text:

```
Instruct: Given the title and abstract of a patent, represent it for clustering by technology field
Query:
```

EmbeddingGemma does not support float16, so it runs in bf16. Models with a context of 8k tokens or more were capped at 2048 tokens; no text in the corpus reaches that length.
The exact model revision, prefix, maximum length and library versions of each run are in the `meta.json` of the model folder.

## Files

Each model folder has three files.

| File | Content |
|---|---|
| `embeddings.npy` | float16 matrix with one row per publication, L2-normalised. Convert to float32 before computing: `X.astype("float32")` |
| `ids.parquet` | `publication_number` and `abstract_is_placeholder` for each row |
| `meta.json` | model id and revision, prefix, maximum length, truncated texts, padding check, run time, library versions |

Because the vectors are normalised, the dot product is the cosine similarity.

## Checks

- Every value is finite and the shape matches `meta.json`.
- Padding check: the embedding of a text computed alone is compared with the same text inside a padded batch. The minimum cosine is in `meta.json` (`padding_check_min_cos`). It is 1.0000 for the fp32 models and between 0.997 and 0.999 for the bf16 models. The script stops below 0.95.

## Run

- One Azure VM with an NVIDIA A100 80GB PCIe, torch 2.6.0+cu124, sentence-transformers 6.3.0, transformers 5.20.2.
- Total time about 35 minutes, 17.5 of them for Qwen3-Embedding-4B.
- The script works in shards of 8,192 rows and resumes after an interruption. A model that fails is reported and the others continue.

To reproduce, from the repository root:

```
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements-embeddings.txt
export HF_TOKEN=...        # EmbeddingGemma is gated: accept its licence on Hugging Face first
python src/generate_embeddings.py
```

`--models` selects some models, `--limit N` embeds only the first N publications, `--out-dir` changes the output folder, `--list` prints the registry.
