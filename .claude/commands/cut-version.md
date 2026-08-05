---
description: Run the pre-release gate for a new immutable benchmark version
argument-hint: <version, e.g. v0.2>
---

Prepare benchmark version **$1** for release. Do not write anything to GCS until every gate below passes.

Work through this checklist and report each line as PASS or FAIL with the actual count or value — never assert a pass you did not measure:

```
Release gate for $1:
- [ ] Target prefix benchmark/$1/ does NOT already exist (releases are immutable)
- [ ] Every item validates against schemas/benchmark_item.schema.json
- [ ] Zero items with label_source of llm_draft or null
- [ ] Zero duplicate item_id; zero duplicate accession_number within a task
- [ ] Every origin=edgar item has source_url, accession_number, cik, fiscal_year
- [ ] Task C clean/deficient counts recorded and roughly balanced
- [ ] Every paraphrased:true item has a resolvable paraphrase_of twin
- [ ] Per-task and per-label counts printed
```

If any line fails, stop and report which. Do not write a partial version and do not "fix" a failing item by relabeling it — a failing label goes back to human review.

On full pass, write the version, then append a changelog entry to `docs/versions.md` recording: version, date, item counts by task and by label_source, what changed from the previous version, and the reason.

Read the `labeling-controls` skill for the taxonomy and provenance rules before starting.
