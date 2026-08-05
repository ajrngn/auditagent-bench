# Notebooks

Authored and executed in **Google Colab** (the working machine is browser-only). This directory holds the exported `.ipynb` files for version control; Colab is the source of truth for execution, git is the source of truth for the code.

## Stages

| File | Reads | Writes | Skill |
|---|---|---|---|
| `01_edgar_fetch.ipynb` | EDGAR APIs | `gcs://<bucket>/raw/` | `edgar-harvesting` |
| `02_extract_item9a.ipynb` | `raw/` | `gcs://<bucket>/processed/` | `edgar-harvesting` |
| `03_labeling_sync.ipynb` | `processed/` ↔ review Sheet | `processed/labels/` | `labeling-controls` |
| `04_build_benchmark.ipynb` | `processed/`, labels | `gcs://<bucket>/benchmark/v0.N/` | `labeling-controls` |
| `05_eval_harness.ipynb` | `benchmark/v0.N/`, `prompts/v1/` | `results/<run_id>/` | `running-evals` |
| `06_analysis.ipynb` | `results/` | `docs/`, `site/results.html` | `running-evals`, `publishing-results` |

## Rules for every notebook

- **Idempotent and resumable.** Check GCS for existing output before doing work. Long runs get interrupted; a re-run must skip what is already done and print skipped-vs-processed counts.
- **No hidden state.** A notebook must produce the same result on a fresh runtime with cells run top to bottom. Nothing may depend on a variable defined in a cell that was later edited.
- **Secrets from Colab Secrets only** (`google.colab.userdata`). Never a literal key in a cell, never a key in GCS.
- **Config in the first cell.** Bucket name, prefixes, dataset version, and model strings go in one cell at the top, not scattered through the notebook.
- **Clear outputs before export.** Committed notebooks carry code, not stale run output — with one exception: `06_analysis` may retain charts referenced by the write-up.
- Shared helpers that more than one notebook needs go in `src/` and are imported, not copy-pasted.

## Exporting to this directory

Colab → File → Download → `.ipynb`, then place here with the exact filename above. Keep the numeric prefix; ordering is the dependency order.
