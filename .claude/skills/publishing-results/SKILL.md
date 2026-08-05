---
name: publishing-results
description: Drafts the public artifacts for AuditAgent Bench - GitHub README, HuggingFace dataset card, auditagent.ca site copy, results write-up, and the ISACA-style article. Use when writing documentation, a dataset card, a paper or blog draft, release notes, contamination-policy disclosure, or any text that will be published under the AuditAgent Bench name.
---

# Publishing results

Everything here is public and permanent. The credibility of the benchmark rests entirely on whether the write-up is honest about its limits.

## Never, in any published artifact

- **No number that was not produced by a logged run.** Every figure traces to a `results/<run_id>/manifest.json`. No estimates, no "approximately", no illustrative placeholders in a draft that could survive to publication. Write `TK` for a pending number so it is impossible to miss.
- **No employer data or affiliation implying employer endorsement.** This is independent work using public SEC data.
- **No claim of novelty that has not been checked.** The claim is specific: no existing benchmark uses SEC Section 404 material weakness disclosures as labeled data for control evaluation. Do not inflate it to "first audit benchmark" — AuditBench and FinVerBench exist and cover statement/numerical error detection.
- **No verbatim COSO or PCAOB framework text.**

## Required disclosures in every results write-up

State all of these, prominently, not in a footnote:

1. **Contamination.** EDGAR filings are in every evaluated model's training data. List all three mitigations and report both scores: verbatim and paraphrased subset. State plainly that Task B (synthetic) is the only contamination-free reasoning measure.
2. **Label provenance.** Break items down by `label_source`. Say how many labels came from the filer's own characterization versus human judgment.
3. **Prompt sensitivity.** One prompt template per task, versioned. Say that results are not comparable across prompt versions and give the version used.
4. **Sample construction.** The EDGAR full-text query, fiscal-year range, and the clean/deficient split — enough for someone to rebuild the sample.
5. **Known limitations.** English-only, US filers, no ITGC scenarios in v1, no tool-use or multi-agent evaluation, no fine-tuning comparison.

## Licensing — decided, do not revisit

- Dataset: **CC-BY 4.0** (EDGAR source text is public domain)
- Code and harness: **MIT**

Do not introduce a dependency under a license incompatible with either.

## Artifacts and where they live

| Artifact | Location | Notes |
|---|---|---|
| Repo README | `README.md` | Quickstart, task definitions, license, citation block |
| Dataset card | `docs/dataset-card.md` | HuggingFace format; mirrors README plus per-field schema |
| Results write-up | `docs/results-v<n>.md` | One per benchmark version |
| Site copy | `site/` | See `reference/site-and-domain.md` |
| ISACA article draft | `docs/article-draft.md` | Practitioner audience — see voice notes below |

## Voice

Two audiences, one document set. Internal audit practitioners (ISACA readership) know COSO and AS 2201 cold and do not know eval methodology. ML researchers are the reverse.

- Define eval terms (false-positive rate, contamination, held-out set) on first use. Do not define material weakness or segregation of duties.
- Lead with the finding, then the method. Practitioners want the number that changes their view of using LLMs on control work.
- Plain declaratives. No hype about AI capability in either direction — the whole value of the benchmark is that it measures instead of asserting.
- Report unflattering results as prominently as flattering ones. A high false-positive rate on clean controls is the most useful thing this benchmark can find.

## Citation block

Keep a `CITATION.cff` and a BibTeX block in the README, versioned to match the benchmark version.
