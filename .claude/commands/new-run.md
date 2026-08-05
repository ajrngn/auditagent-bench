---
description: Set up and launch an eval run with a complete manifest
argument-hint: <task A|B|C|D> <model string> [dataset version]
---

Set up an eval run for task **$1** using model **$2** on dataset version **$3** (default: the latest released version).

Before submitting a single request:

1. Confirm the model string is a full pinned identifier. Reject an alias or `latest` — a recorded result must be reproducible.
2. Read the prompt template for task $1 from `prompts/v1/` and compute its SHA-256.
3. Build `results/<run_id>/manifest.json` with: `run_id`, `task`, `model_string`, `vendor`, `prompt_version`, `prompt_sha256`, `dataset_version`, `n_items`, `run_started_at`, `batch`. Write it **before** the run starts.
4. Confirm the batch API is being used unless there is a stated reason not to.
5. Estimate and report the token cost for the full item set.

During the run:

- Write every raw response to `results/<run_id>/raw/<item_id>.json` **before** parsing it.
- Strip markdown fences, then `json.loads` inside try/except. On a parse failure, log the raw text, mark the item `parse_failed`, and continue. Do not regex an answer out of prose.
- Run the full item set. No sampling.

Report at the end: items completed, `parse_failed` count, elapsed time, and the run directory path. Report the parse-failure count as a finding, not an error to hide.

Read the `running-evals` skill before starting.
