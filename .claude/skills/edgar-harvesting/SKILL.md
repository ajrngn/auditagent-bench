---
name: edgar-harvesting
description: Fetches SEC EDGAR 10-K filings and extracts Item 9A internal-control text into versioned JSONL on GCS. Use when writing or debugging the 01_edgar_fetch or 02_extract_item9a notebooks, querying efts.sec.gov or data.sec.gov, handling SEC rate limits or User-Agent errors, parsing filing HTML, or resuming an interrupted EDGAR pull.
---

# EDGAR harvesting

Covers pipeline stages 01 (fetch) and 02 (extract). Output contract: one JSONL record per filing in `gcs://<bucket>/processed/`.

## SEC access rules — these are policy, not style

- **Every request must set a descriptive `User-Agent`** with a real contact address, or SEC returns 403:
  `AuditAgent Bench (ajrngn@gmail.com)`
- **Cap at ~10 requests/second.** Sleep between requests. A burst gets the IP blocked, not throttled.
- No API key exists and none is needed. If code asks for an EDGAR key, it is wrong.
- Endpoints: full-text search `https://efts.sec.gov/LATEST/search-index?q=...`, submissions `https://data.sec.gov/submissions/CIK##########.json`, filing documents under `https://www.sec.gov/Archives/edgar/data/<cik>/<accession-no-dashes>/`.

## Idempotence is mandatory

Long pulls get interrupted. Before fetching anything, check whether the output already exists in GCS and skip it.

```python
def already_done(bucket, prefix, accession):
    return bucket.blob(f"{prefix}/{accession}.json").exists()
```

Rules:
- Key every artifact by `accession_number` — it is the only stable unique ID. Not CIK, not ticker, not URL.
- Write each record as its own blob during fetch; concatenate to JSONL only in stage 02. A single append-mode JSONL is not resumable.
- Log skipped-vs-fetched counts at the end of every run.
- Never re-download a filing that is already in `raw/` just to re-parse it. Re-parsing reads from `raw/`.

## Item 9A extraction

Item 9A ("Controls and Procedures") boundaries are inconsistent across filers. Extract by locating the heading, then reading to the next `Item` heading.

- Parse with BeautifulSoup. Strip `<script>`, `<style>`, and XBRL `<ix:header>` before text extraction.
- Match headings case-insensitively and tolerate `ITEM 9A.`, `Item 9A(T)`, and non-breaking spaces.
- **Reject, do not guess.** If the heading is not found, or the extracted span is under ~500 characters, or the next-item boundary is missing, write the record to a `extraction_failed` list with the reason. Do not emit a truncated or whole-document fallback into `processed/`.
- Record extraction failures with counts. A silently degraded corpus is the main quality risk in this stage.

## Required fields on every record

`source_url`, `accession_number`, `cik`, `company_name`, `fiscal_year`, `form_type`, `filing_date`, `item_9a_text`, `extraction_method`, `fetched_at`.

Labels are **not** assigned here. Stage 01/02 produce unlabeled text only — labeling happens in `03_labeling_sync`. See the `labeling-controls` skill.

## Sampling targets (v1)

~500 filings: ~250 disclosing a material weakness (found via full-text search for "material weakness", form type 10-K) and ~250 clean. Prioritize fiscal years 2025–2026 for the contamination policy. Record the search query used in the run manifest — the sample must be reproducible.
