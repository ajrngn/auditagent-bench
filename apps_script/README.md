# Apps Script — review sheet writeback

The Google Sheet half of stage 03. This is the **only** path that stamps `label_source` on a benchmark item.

## Setup

1. Open the review sheet → **Extensions → Apps Script**.
2. Paste `Code.gs` into the editor.
3. **Project Settings → Show `appsscript.json`**, then replace it with the copy here (it declares the GCS scope).
4. **Project Settings → Script Properties**, add:
   - `GCS_BUCKET` — the bucket name
   - `GCS_LABEL_PREFIX` — optional, defaults to `processed/labels`
5. Run `authorizeOnce` from the editor and accept the scope prompt.
6. Reload the sheet. An **AuditAgent** menu appears.

The Google account running the script needs `roles/storage.objectCreator` on the bucket.

## Sheet columns

`item_id`, `accession_number`, `company_name`, `fiscal_year`, `item_9a_text`, `severity`, `coso_component`, `is_deficient`, `reviewed`, `reviewer_notes`

Stage 03 writes the header row and appends candidates. Set data validation dropdowns on `severity` and `coso_component` from the taxonomy in the `labeling-controls` skill, and a checkbox on `reviewed`.

`item_9a_text` is truncated to 45,000 characters on push — Sheets caps a cell at 50,000.

## Menu actions

**Validate reviewed rows** — reports how many rows are ticked and which are incomplete. Writes nothing. Run this first.

**Export reviewed rows to GCS** — writes ticked *and* complete rows to `processed/labels/reviewed.jsonl`, stamping `label_source` and `reviewed_at`. Incomplete rows are skipped, not exported with blanks.

## Why the stamping lives here

`label_source` records whether a human actually reviewed a label. If notebook code could write `llm_draft_human_verified`, that field would stop meaning anything — a pipeline run could mark thousands of unreviewed items as verified. Binding the stamp to a menu action a reviewer clicks, on a row a reviewer ticked, is what makes the field trustworthy.

Stage 03's pull step refuses to export reviewed rows that carry no `label_source`, which catches the case where someone ticks boxes but never runs the export.
