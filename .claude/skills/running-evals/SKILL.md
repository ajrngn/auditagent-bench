---
name: running-evals
description: Runs the multi-vendor eval harness for AuditAgent Bench and scores Tasks A-D. Use when writing or debugging the 05_eval_harness or 06_analysis notebooks, editing prompt templates, calling Vertex/OpenAI/first-party model APIs or their batch endpoints, parsing structured JSON model output, computing benchmark metrics, or comparing results across runs.
---

# Running evals

Stage 05 (harness) and 06 (analysis). One run produces `results/<run_id>/` containing `raw/`, `scored.jsonl`, and `manifest.json`.

## Run manifest — write this before scoring, not after

Every run directory MUST contain `manifest.json` with:

```json
{
  "run_id": "2026-08-05T14-30_taskA_sonnet",
  "task": "A",
  "model_string": "claude-sonnet-4-6",
  "vendor": "anthropic",
  "prompt_version": "v1",
  "prompt_sha256": "<hash of the exact template file>",
  "dataset_version": "benchmark/v0.1",
  "n_items": 312,
  "run_started_at": "2026-08-05T14:30:00Z",
  "batch": true
}
```

Without a manifest, a result is unpublishable. Two numbers that came from different prompt versions are not comparable, and there is no way to reconstruct which was which after the fact.

## Non-negotiables

- **Log every raw response to `results/<run_id>/raw/<item_id>.json` before parsing it.** Scoring bugs are recoverable; lost responses mean re-paying for the whole run.
- **Full item set, every model.** No sampling shortcuts in anything that gets released.
- **Pin full model strings** (`claude-sonnet-4-6`, `gemini-2.5-pro-002`) — never an alias, never `latest`. Record vendor + model string + run date in the manifest.
- **A prompt change is a new results version.** Bump `prompt_version` and re-run everything; never mix.
- Cross-vendor coverage is required for credibility: Anthropic first-party, Gemini via Vertex, OpenAI, and an open-weights model via Vertex Model Garden. A result set covering one vendor is not a benchmark.
- **Prefer batch APIs.** Nothing here is latency-sensitive and batch pricing roughly halves cost.

## Parsing model output

Request JSON explicitly in the prompt. Then, in order:

1. Strip markdown fences (```json ... ```) — models add them even when told not to.
2. `json.loads` inside `try/except`.
3. On failure: log the raw text with the item ID, mark the item `parse_failed`, and continue. **Do not regex the answer out of prose** — a salvaged answer is a different measurement than a returned answer.
4. Report `parse_failed` count as a first-class metric per model. A model that cannot produce parseable JSON is a real finding, not a bug to paper over.

Validate the parsed object against the task's expected keys before scoring. An unexpected key set counts as `parse_failed`, not as a wrong answer.

## Metrics by task

| Task | Primary metric | Also report |
|---|---|---|
| A — Deficiency classification | Accuracy vs. severity label | 3x3 severity confusion matrix; COSO component accuracy |
| B — Control design evaluation | Accuracy on designed-effectively | Gap-type accuracy (SoD / precision / evidence / timeliness) |
| C — Clean/dirty discrimination | **False-positive rate on clean items** (headline) | Recall on deficient items, F1 |
| D — Standards citation | Citation precision | Hallucinated-citation rate |

Task C's FP rate is the headline number for the whole benchmark. FinVerBench reported 95–100% FP rates on clean financial statements; the open question is whether that holds for controls. Report it prominently even when it is unflattering.

Always report the paraphrased-subset score alongside the verbatim score (contamination control), and treat Task B as the contamination-free reasoning baseline.

## Cost and failure handling

- Estimate token cost before launching a full cross-vendor run and state the number.
- Batch jobs fail partway. Make submission resumable by item ID, same pattern as `edgar-harvesting`.
- Store API keys in Colab Secrets only.
