---
license: cc-by-4.0
language:
  - en
task_categories:
  - text-classification
tags:
  - internal-audit
  - sox-404
  - internal-control
  - coso
  - sec-edgar
  - finance
  - benchmark
size_categories:
  - n<1K
pretty_name: AuditAgent Bench
---

# Dataset card — AuditAgent Bench

<!--
  Every number in this card must trace to a released benchmark version and its
  gate report. Use TK for a pending figure so it is impossible to miss.
  Do not estimate. See the `publishing-results` skill.
-->

**Version:** UNRELEASED · **Items:** TK · **Released:** TK

## Summary

AuditAgent Bench measures how well language models evaluate **internal controls** under Section 404 of the Sarbanes-Oxley Act. Existing financial benchmarks test error detection in financial statements; this one tests control evaluation — severity classification, design assessment, clean/deficient discrimination, and standards citation.

Items for Tasks A, C, and D are derived from Item 9A ("Controls and Procedures") disclosures in 10-K filings on SEC EDGAR. Task B items are original, hand-authored control-design scenarios.

## Tasks

| Task | Input | Target | Origin |
|---|---|---|---|
| A | Disclosed control weakness | `severity` (3-way) + `coso_component` (5-way) | EDGAR |
| B | Process narrative + control description | `designed_effectively` + `gap_type` (6-way) | Synthetic |
| C | Item 9A disclosure | `is_deficient` (binary) | EDGAR |
| D | Identified deficiency | `citation` (COSO principle or PCAOB standard) | EDGAR |

**Headline metric: false-positive rate on clean items in Task C** — the share of genuinely clean disclosures a model incorrectly flags as deficient. Prior work on financial-statement error detection reported false-positive rates of 95–100% on clean inputs for most models; whether that behavior persists on control evaluation is the question this benchmark was built to answer.

## Fields

Full schema: [`schemas/benchmark_item.schema.json`](../schemas/benchmark_item.schema.json).

| Field | Type | Notes |
|---|---|---|
| `item_id` | string | `<task letter>-<4 digits>`, e.g. `C-0142` |
| `task` | enum | `A` \| `B` \| `C` \| `D` |
| `input` | object | Shape varies by task |
| `label` | object | Ground truth; populated keys vary by task |
| `label_source` | enum | `disclosure` \| `human` \| `llm_draft_human_verified` |
| `paraphrased` | bool | True for contamination-control twins |
| `paraphrase_of` | string | `item_id` of the verbatim twin |
| `provenance` | object | `origin`, plus `source_url`, `accession_number`, `cik`, `fiscal_year` for EDGAR items |

## Label provenance

Every ground-truth label in a released version is human-reviewed. `label_source` records how each was produced:

| Value | Count |
|---|---|
| `disclosure` — the filer's own characterization | TK |
| `human` — assigned by a reviewer | TK |
| `llm_draft_human_verified` — model-drafted, reviewer-accepted | TK |

Models may draft candidate labels; none ships without review. The release gate hard-fails on any item lacking a human-reviewed provenance value.

## Contamination

EDGAR filings are in the training data of every model this benchmark evaluates. This is disclosed rather than assumed away. Three mitigations:

1. Recent fiscal years are prioritized, past the training cutoff of most evaluated models.
2. A paraphrased subset (TK items) is maintained. Both verbatim and paraphrased scores are reported; the gap between them separates memorization from reasoning.
3. Task B items are synthetic and contamination-free by construction — the reasoning control group.

## Limitations

- English-language filings from US registrants only.
- v1 excludes IT general control (ITGC) scenarios.
- No fine-tuning, tool-use, or multi-agent evaluation.
- **Task A labels inherit the filer's own severity characterization**, which is a judgment made under disclosure incentives, not an independent determination.
- **Clean items are presumed clean because no weakness was disclosed** — an absence of disclosure, not independent verification. A filer that failed to identify a weakness appears clean here.
- Task D citations reference COSO principle and PCAOB standard numbers; framework text is not reproduced, so a model cannot be scored on quoting it.

## Uses

Intended for evaluating and comparing model performance on internal-control assessment, and for research on where such models fail.

**Not intended** as a substitute for professional judgment in an actual ICFR assessment, as evidence in an audit, or as a source of authoritative interpretation of COSO or PCAOB standards.

## Licensing

Dataset: CC-BY 4.0 ([LICENSE-DATA](../LICENSE-DATA)). Harness code: MIT ([LICENSE](../LICENSE)).

EDGAR source text is a public record. What is licensed is the compilation: filing selection, extracted spans, labels, and paraphrases.

## Citation

See [CITATION.cff](../CITATION.cff). Cite the version — released versions are immutable, so the version number identifies exactly which items were used.
