# AuditAgent Bench

A public benchmark evaluating how well large language models perform internal-control (SOX 404) assessment tasks.

Existing financial benchmarks (AuditBench, FinVerBench) test error detection in financial statements. This one tests **control evaluation**: deficiency classification, control design assessment, clean/dirty discrimination, and standards citation — using SEC Section 404 material weakness disclosures as labeled data.

**Status:** dataset construction. No benchmark version released yet.

## Tasks

| Task | Input | Output | Source |
|---|---|---|---|
| A | Disclosed control weakness | Severity + COSO component | EDGAR Item 9A |
| B | Process narrative + control description | Designed effectively? + gap type | Synthetic, hand-labeled |
| C | Mixed clean and deficient Item 9A text | Deficient / clean flag | EDGAR Item 9A |
| D | Identified deficiency | COSO principle / PCAOB standard citation | EDGAR Item 9A |

Task C's **false-positive rate on clean items** is the headline metric.

## Repository layout

```
notebooks/        one notebook per pipeline stage, 01..06
prompts/v1/       versioned prompt templates, one per task
schemas/          JSONL record schemas
src/              shared helpers: gcs, edgar, parsing, schema
scripts/          one-off ops run from CI, not part of the pipeline
apps_script/      Google Sheet writeback — the only path that stamps label_source
.github/          Pages deploy on push; manual DNS sync
results/          per-run outputs: manifest.json, scored.jsonl, raw/ (gitignored)
docs/             dataset card, results write-ups, article drafts
site/             auditagent.ca static site (GitHub Pages)
.claude/skills/   agent skills for each pipeline stage
```

Data itself lives in GCS, not git: `raw/` → `processed/` → `benchmark/v0.N/` → `results/`.
Released benchmark versions are **immutable**.

## Pipeline

| Notebook | Does | Reads | Writes |
|---|---|---|---|
| `01_edgar_fetch` | Search + download 10-Ks | EDGAR APIs | `gcs://<bucket>/raw/` |
| `02_extract_item9a` | Extract Item 9A text | `raw/` | `gcs://<bucket>/processed/` |
| `03_labeling_sync` | Push candidates to review sheet, pull verified labels back | `processed/` ↔ Sheet | `processed/labels/` |
| `04_build_benchmark` | Validate + cut an immutable version | `processed/`, labels | `benchmark/v0.N/` |
| `05_eval_harness` | Run models across all tasks | `benchmark/v0.N/`, `prompts/` | `results/<run_id>/` |
| `06_analysis` | Score, chart, generate `site/results.html` | `results/` | `docs/`, `site/` |

Every notebook is idempotent and resumable — check GCS for existing output before doing work.

## Constraints

- **Browser/cloud only.** Development happens on a locked-down machine: Colab, Apps Script, and GCP services. No local servers, no desktop installs.
- **Public data only.** SEC EDGAR or synthetic. No employer data, ever.
- **Human-verified labels only.** Models may draft; a person reviews before anything is released.

## Licensing

Dataset: **CC-BY 4.0** (EDGAR source text is public domain). Code and harness: **MIT**.

COSO 2013 and PCAOB AS 2201 are referenced by principle/standard number for the label taxonomy. Their text is not reproduced.

## Out of scope for v1

Fine-tuning, financial-statement error detection, multi-agent or tool-use evaluation, non-English filings, and ITGC-specific scenarios (candidate for v2).
