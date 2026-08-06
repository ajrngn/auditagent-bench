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

## Search results: what the API actually returns

Verified against live EDGAR, not assumed:

- The field is **`root_forms`** (a list), not `root_form`. `_source.form` carries the actual type; `root_forms[0]` carries the base form.
- **`forms=10-K` does not exclude amendments.** It matches `root_forms`, so a 10-K/A has `root_forms: ["10-K"]` and comes back. Filter on `form_type == "10-K"` explicitly.
- This bias is not random: amendments are frequently filed *because* of a restatement, so `"material weakness"` matches them strongly. An unfiltered sample of 6 returned **6 amendments**. Amendments are partial refilings — short, no Item 9B/10 boundary, sometimes no Item 9A at all.
- `_source.adsh` is the accession number directly. `_id` is `"<accession>:<filename>"` and names the exact document that matched — use it rather than scanning `index.json` for a likely primary document.

`edgar.hit_to_record()` handles all of this. Use it instead of reaching into `_source` by hand.

## Item 9A extraction

Item 9A ("Controls and Procedures") boundaries are inconsistent across filers. Extract by locating the heading, then reading to the next `Item` heading.

- Parse with BeautifulSoup. Strip `<script>`, `<style>`, and XBRL `<ix:header>` before text extraction.
- Match headings case-insensitively and tolerate `ITEM 9A.`, `Item 9A(T)`, and non-breaking spaces.
- Search heading matches **in reverse** — the last occurrence is the section, earlier ones are the table of contents.
- Boundary headings are Item 9B, Item 9C, Item 10, Part III/IV, and the signature block. Filings that end at Item 9A have none of these; those fall back to a 60,000-char cap and are recorded as `extraction_method: heading_to_end`.
- **Reject, do not guess.** If no heading is found, or no span reaches 500 characters, write the record to an `extraction_failed` list with the reason. Never emit a whole-document fallback into `processed/`.
- Record extraction failures with counts. A silently degraded corpus is the main quality risk in this stage.

### Success rate is not usable-item rate

Measured on 8 original 10-Ks: **8/8 extracted**, but of those —

- one hit the 60,000-char cap (`heading_to_end`, no boundary found) — over-capture, not a section
- two were cross-reference stubs: Item 9A pointing at the financial statements rather than containing substantive disclosure
- one showed `CONTROL S AND PROCEDURES`, where inline formatting tags split a word during text extraction

Expect yield from a 500-filing pull to be well below 500. Flag records at the length cap and records under ~2,000 characters for review before they reach the labeling sheet.

## Beyond the 10-K: three more EDGAR surfaces

**20-F and 40-F.** Foreign private issuers registered with the SEC file management's ICFR report under the same rules and the same COSO 2013 criteria, with auditor attestation for non-EGC accelerated and large accelerated filers. 40-F is the MJDS form used by Canadian issuers.

This is how international coverage is obtained. It costs new heading logic and nothing else — no new API, no new auth, no scraping. Be precise about what the sample *is*: a 40-F filer is a Canadian company complying with **SOX**, not with NI 52-109. That broadens the company population, not the regulatory population, and the record carries `jurisdiction: CA` with `regime: sox_404` to keep the two from being conflated.

The ICFR section sits at a different place per form — `icfr_item` records which, so a parser regression can be traced to the form it broke on:

| Form | Section | `icfr_item` |
|---|---|---|
| 10-K | Item 9A | `item_9a` |
| 20-F | Item 15 | `item_15` |
| 40-F | Controls disclosure, outside the numbered-item scheme | `form_40f_controls` |

Boundary headings differ per form. The current extractor's boundaries are 10-K specific; 20-F and 40-F need their own before those forms are fetched.

**Item 4.02 8-K — non-reliance.** "Non-Reliance on Previously Issued Financial Statements." A 4.02 filed after a clean 10-K is direct evidence the clean assertion was wrong. Set `subsequent_non_reliance` and record the contradicting accession, so the exclusion is auditable rather than asserted.

This is not optional polish. Task C's headline metric is the false-positive rate on clean items, and a restated filing sitting in the clean pool means a model that correctly flags it gets scored as wrong. See the clean-label policy in `CLAUDE.md`.

**Comment letters — `UPLOAD` and `CORRESP`.** Staff letters to filers and filer responses, released roughly 20 business days after review completes. Search via full-text search with the **"Filing review correspondence"** filing category.

These are cases where SEC staff *questioned a filer's own ICFR conclusion*, with reasoning attached — a documented third-party disagreement with a management assertion, which nothing else in the pipeline provides.

## Required fields on every record

`source_url`, `accession_number`, `cik`, `company_name`, `fiscal_year`, `form_type`, `jurisdiction`, `regime`, `filing_date`, `icfr_text`, `icfr_item`, `extraction_method`, `fetched_at`.

Record `auditor_attested` and `filer_status` where determinable — they drive `clean_confidence` downstream, and a management-only assertion is a materially weaker evidence standard than an attested one.

Labels are **not** assigned here. Stage 01/02 produce unlabeled text only — labeling happens in `03_labeling_sync`. See the `labeling-controls` skill.

## Sampling targets (v1)

~500 filings: ~250 disclosing a material weakness (found via full-text search for "material weakness") and ~250 clean. Prioritize fiscal years 2025–2026 for the contamination policy. Record the search query used in the run manifest — the sample must be reproducible.

Run **20 filings first, not 500.** The measured yield on a sample of 8 was 8/8 extracted but only 5 usable. Twenty tells you the real rate before committing to a long pull, and the rate is what determines whether ~500 filings reaches the 300–400 item target.
