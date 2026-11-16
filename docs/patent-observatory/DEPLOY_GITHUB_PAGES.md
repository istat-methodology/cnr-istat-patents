# Publish the Patent Semantic Observatory on GitHub Pages

## Option A — quickest: publish the STARTER dashboard today

The starter package already includes all quantitative tables, interactive charts, 2 actual pilot UMAP maps (BGE-M3 and Patent SBERT), plus hover/click patent diagnostics for all nine models. It does **not** yet contain the other seven UMAP HTML files, so those two maps are the only ones listed as available in the 2D UMAP tab.

1. Download `istat_cnr_patent_observatory_starter.zip`.
2. **Unzip it** on your Mac. You should see `index.html`, `assets/`, `data/`, `maps/`, `downloads/`, and Markdown instructions. Do **not** upload the ZIP itself and expect GitHub Pages to unzip it.
3. At **https://github.com/new**, create a **public** repository, e.g. `istat-cnr-patent-observatory` (you can use your own account or an approved institutional organization).
4. In the repository, choose **Add file → Upload files**. Drag the **contents** of the unzipped folder into the upload area, preserving the directory structure. Commit to the `main` branch. Verify that `index.html` is shown at the repository root.
5. In the repository, open **Settings → Pages**. Under **Build and deployment**, choose **Source: Deploy from a branch**, **Branch: main**, **Folder: /(root)**, then **Save**.
6. When GitHub Pages reports deployment, open its displayed site URL. For a project repository the URL usually has the form `https://YOUR_USERNAME.github.io/istat-cnr-patent-observatory/`.
7. Test the **Embedding comparison** plots, **Explore patents → Patent SBERT → 2D UMAP** click-to-read functionality, and a **Centroid-distance diagnostic** under a model whose UMAP hasn't yet been added.

## Option B — recommended: import all nine UMAP maps before publishing

Notebook 14 already saved all nine UMAP maps to Google Drive, so **no computation needs to be repeated**.

1. Download `istat_cnr_patent_observatory_starter.zip` and the companion `15_complete_dashboard_maps_colab.ipynb` (both are supplied in the response; the notebook is also included in `scripts/`).
2. Open the companion notebook in **Google Colab** (File → Upload notebook).
3. Run all cells. The notebook will mount Google Drive and look for the maps under:

   `MyDrive/istat_patents/semantic_results_v11_clustering_robustness/pilot_200_per_field/all_texts/interactive/`

4. When requested, upload the starter ZIP from your computer (or put it in `MyDrive/istat_patents/dashboard_publish/` first).
5. It will import available map HTMLs, adjust their local Plotly reference, and save/download `istat_cnr_patent_observatory_complete.zip` to/from:

   `MyDrive/istat_patents/dashboard_publish/`

6. Unzip this **complete** ZIP and follow Option A steps 3–7. You should see UMAPs available for **all nine** models.

If a map is missing, the Colab notebook reports its exact expected path and does not invent coordinates. You can rerun **only Notebook 14's interactive export cell** for that model if needed.

## Update a website later

After adding maps or modifying the dashboard, upload the changed site files to the same GitHub repository and commit. GitHub Pages republishes from the configured branch automatically; you don't need to change Pages settings again.

## Privacy and institutional permissions

**GitHub Pages makes the site's HTML, JS and embedded patent titles/abstracts publicly accessible.** The embedding source is public, but you should still check the project's publication and attribution policy. The dashboard does not include any Hugging Face private token, Google credentials or proprietary model weights. Do not upload confidential documents or raw unreleased datasets.

## Scientific restrictions to mention in presentations

- Full-corpus benchmark: 63,968 patents, nine representations, K=8/16.
- Alternative-method comparison: pilot of 6,400 patents.
- Interactive 2D UMAP maps: **2,400 pilot patents**, independently projected per embedding model.
- Review candidates: deliberately selected patents, not a statistically representative validation study.
- It is not yet established that the sample is *more heterogeneous than an earlier sampling approach*: that needs a direct sample comparison.

Official GitHub instructions: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
