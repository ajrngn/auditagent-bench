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

- **COSO component:** the five 2013 components — control environment, risk assessment, control activities, information & communication, monitoring activities. **This is Task A's primary label**, because it is jurisdiction-neutral and well-populated across every source.
- **Severity:** `deficiency` | `significant_deficiency` | `material_weakness`. Definitions follow PCAOB AS 2201; when the source's own language is ambiguous, mark `reviewer_notes` and leave severity blank rather than guessing.
- **Task B gap types:** segregation of duties, precision, evidence, timeliness, management review, access.

**Do not reproduce COSO 2013 or PCAOB AS 2201 text verbatim in the dataset.** They are reference frameworks for the taxonomy, not licensed content to redistribute. Paraphrase; cite the principle number.

### Severity is only scored where a gradient could exist

SEC rules compel disclosure of **material weaknesses only**. Significant deficiencies go to the audit committee; lower deficiencies are never reported. So a severity label taken from a 10-K, 20-F, or 40-F is almost always `material_weakness` — not because that reflects reality, but because that is the only tier disclosure rules surface.

Set `label.gradient_bearing`:

| Source | `gradient_bearing` | Why |
|---|---|---|
| Single Audit finding | `true` | Findings are explicitly classified MW or SD |
| Synthetic scenario | `true` | The author chose the severity |
| 10-K / 20-F / 40-F | `false` | Near-entirely material weakness |
| Comment letter | `false` | Staff question the conclusion, not the tier |

Score severity on the `true` subset alone. Scoring it corpus-wide measures the sampling frame, not the model. `release_gate` fails if a `sec_periodic` item claims `gradient_bearing: true`.

### Rating clean items

A clean label means nobody disclosed a weakness — absence of disclosure, not absence of deficiency. Every Task C clean item needs `clean_confidence`:

- **`attested`** — an auditor issued an ICFR opinion behind the assertion. Accelerated and large accelerated non-EGC filers. **The headline false-positive rate is computed on this subset only.**
- **`management_only`** — management's assertion with no 404(b) attestation. Reported alongside, labelled as the weaker measurement it is.
- **`excluded_restated`** — a later Item 4.02 8-K or subsequent-period material weakness contradicts the clean label. **Must not reach a release.**

The reviewer does not decide `attested` vs `management_only` by judgment — it follows from `auditor_attested` on the filing record. What the reviewer decides is whether the disclosure genuinely reads as clean.

## Cutting a version

Releases live at `gcs://<bucket>/benchmark/v0.1/`, `v0.2/`, ... and are **immutable**. Never overwrite a released prefix — if something is wrong, cut a new version and note the fix in the changelog.

Before writing a version, `04_build_benchmark` must verify:

- [ ] Every item validates against `benchmark_item.schema.json`
- [ ] Zero items with `label_source` of `llm_draft` or null
- [ ] No duplicate `item_id`, no duplicate `accession_number` within a task
- [ ] Every item carries `provenance.origin`, `jurisdiction`, `regime`
- [ ] Zero `clean_confidence: excluded_restated` items
- [ ] Every Task C clean item has a `clean_confidence` value
- [ ] The `attested` clean subset is large enough to report on (≥30)
- [ ] No `sec_periodic` item claims `gradient_bearing: true`
- [ ] Every synthetic item has `provenance.drafted_by` set
- [ ] Minimal pairs are complete — both `control` and `variant` present for each `minimal_pair_id`
- [ ] Task C clean/deficient split is recorded and roughly balanced
- [ ] Paraphrased-subset items are flagged with `paraphrased: true` and linked to their verbatim twin via `paraphrase_of`
- [ ] Target prefix does not already exist
- [ ] Row count, per-label counts, provenance breakdown, and clean-confidence breakdown printed and logged to the version changelog

`src/schema.py::release_gate` implements these. Fail the build on any unchecked box. Do not write a partial version, and never relabel a failing item to make the gate green — a failing label goes back to human review.
