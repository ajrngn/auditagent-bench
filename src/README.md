# src/

Shared helpers imported by the Colab notebooks. Anything used by more than one notebook lives here instead of being copy-pasted.

| Module | Contents |
|---|---|
| `gcs.py` | Bucket client, `blob_exists` (the resumability check), JSON/JSONL read and write, `require_absent` guard for immutable release prefixes |
| `edgar.py` | Throttled SEC session with the required `User-Agent`, full-text search paging, accession-number normalization, primary-document resolution |
| `parsing.py` | Fence stripping and `parse_json_response` for model output; `extract_item_9a`, which raises `ExtractionFailure` rather than returning a partial span |
| `schema.py` | Validation against `schemas/*.json` and `release_gate`, the pre-release check `04_build_benchmark` must pass |

These have not been executed — there is no Python on the authoring machine, so they are unverified until first run in Colab.

Notebooks pull this in via a `git clone` or `%pip install -e` cell at the top; keep imports free of local-machine assumptions.
