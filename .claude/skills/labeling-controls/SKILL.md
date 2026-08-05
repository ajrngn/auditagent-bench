---
name: labeling-controls
description: Manages the ground-truth labeling loop for AuditAgent Bench - Google Sheet review UI, Apps Script sync to GCS, label taxonomy, and label provenance. Use when writing or debugging 03_labeling_sync or 04_build_benchmark, writing Apps Script, setting label or label_source fields, assigning COSO components or severity levels, cutting a benchmark version, or reviewing whether an item is ready for release.
---

# Labeling controls

Stage 03 (labeling sync) and 04 (benchmark build). Turns unlabeled Item 9A text plus synthetic scenarios into a released, versioned, human-verified dataset.

## The one rule that cannot bend

**No item enters a released benchmark version unless a human reviewed its label.**

`label_source` records how the label was produced and is required on every item:

| Value | Meaning | Releasable |
|---|---|---|
| `disclosure` | Read directly from the filer's own characterization in Item 9A | Yes |
| `human` | Authored or assigned by a human reviewer | Yes |
| `llm_draft_human_verified` | LLM drafted it, a human reviewed and accepted it | Yes |
| `llm_draft` | LLM output, not yet reviewed | **No** |

An LLM — including you — may draft candidate scenarios and candidate labels. Writing `llm_draft_human_verified` on an item no human has actually reviewed falsifies the dataset. Never set that value programmatically; it is only ever written by the Apps Script path that a reviewer triggers from the sheet. `04_build_benchmark` MUST hard-fail if any item carries `llm_draft` or a missing `label_source`.

## Labeling UI is a Google Sheet. Do not build an app.

The reviewer works on a browser-only corporate laptop. The loop is:

1. `03_labeling_sync` writes candidate rows from `processed/` to the review sheet (one item per row, Item 9A text in a wrapped cell, dropdowns for severity and COSO component, a `reviewed` checkbox, and a `reviewer_notes` column).
2. A human reviews in the browser and ticks `reviewed`.
3. Apps Script writes only `reviewed`-ticked rows back to `gcs://<bucket>/processed/labels/`, stamping `label_source` and `reviewed_at`.

Do not propose a Streamlit app, a Flask labeling tool, Label Studio, or a local UI. That decision is settled.

Sync must be idempotent both directions — re-running stage 03 must not duplicate rows or clobber a reviewer's in-progress edits. Match on `item_id`.

## Taxonomy

- **Severity:** `deficiency` | `significant_deficiency` | `material_weakness`. Definitions follow PCAOB AS 2201; when a filing's own language is ambiguous, mark `reviewer_notes` and leave severity blank rather than guessing.
- **COSO component:** the five 2013 components — control environment, risk assessment, control activities, information & communication, monitoring activities.
- **Task B gap types:** segregation of duties, precision, evidence, timeliness, management review, access.

**Do not reproduce COSO 2013 or PCAOB AS 2201 text verbatim in the dataset.** They are reference frameworks for the taxonomy, not licensed content to redistribute. Paraphrase; cite the principle number.

## Cutting a version

Releases live at `gcs://<bucket>/benchmark/v0.1/`, `v0.2/`, ... and are **immutable**. Never overwrite a released prefix — if something is wrong, cut a new version and note the fix in the changelog.

Before writing a version, `04_build_benchmark` must verify:

- [ ] Every item has `source_url`, `accession_number`, `cik`, `fiscal_year`, `label`, `label_source`
- [ ] Zero items with `label_source` of `llm_draft` or null
- [ ] No duplicate `item_id`, no duplicate `accession_number` within a task
- [ ] Task C clean/deficient split is recorded and roughly balanced
- [ ] Paraphrased-subset items are flagged with `paraphrased: true` and linked to their verbatim twin via `paraphrase_of`
- [ ] Target prefix does not already exist
- [ ] Row count and per-label counts printed and logged to the version changelog

Fail the build on any unchecked box. Do not write a partial version.
