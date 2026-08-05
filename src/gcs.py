"""Google Cloud Storage helpers shared by the pipeline notebooks.

Every pipeline stage is resumable, which means every stage asks "does this output
already exist?" before doing work. That question goes through `blob_exists`.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Iterator

from google.cloud import storage

_client: storage.Client | None = None


def client() -> storage.Client:
    """Cached client. Colab authenticates via google.colab.auth.authenticate_user()."""
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def blob_exists(bucket_name: str, path: str) -> bool:
    return client().bucket(bucket_name).blob(path).exists()


def list_prefix(bucket_name: str, prefix: str) -> list[str]:
    """Blob names under a prefix. Used to compute what a resumed run can skip."""
    return [b.name for b in client().list_blobs(bucket_name, prefix=prefix)]


def write_json(bucket_name: str, path: str, obj: Any) -> None:
    blob = client().bucket(bucket_name).blob(path)
    blob.upload_from_string(
        json.dumps(obj, ensure_ascii=False, indent=2),
        content_type="application/json",
    )


def read_json(bucket_name: str, path: str) -> Any:
    return json.loads(client().bucket(bucket_name).blob(path).download_as_text())


def write_jsonl(bucket_name: str, path: str, records: Iterable[dict]) -> int:
    """Write records as JSONL. Returns the count written.

    Whole-object write, not append: GCS objects are immutable, and an appended
    JSONL cannot be resumed after an interruption. Per-item artifacts during a
    long fetch go to individual blobs; JSONL is a consolidation step.
    """
    records = list(records)
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    blob = client().bucket(bucket_name).blob(path)
    blob.upload_from_string(body + "\n", content_type="application/x-ndjson")
    return len(records)


def read_jsonl(bucket_name: str, path: str) -> Iterator[dict]:
    text = client().bucket(bucket_name).blob(path).download_as_text()
    for line in text.splitlines():
        if line.strip():
            yield json.loads(line)


def write_text(bucket_name: str, path: str, text: str, content_type: str = "text/plain") -> None:
    client().bucket(bucket_name).blob(path).upload_from_string(text, content_type=content_type)


def read_text(bucket_name: str, path: str) -> str:
    return client().bucket(bucket_name).blob(path).download_as_text()


def require_absent(bucket_name: str, prefix: str) -> None:
    """Guard for immutable release prefixes.

    Released benchmark versions are never overwritten. Call this before writing
    a benchmark/vN.N/ prefix; it raises rather than letting a build clobber a
    published version.
    """
    existing = list_prefix(bucket_name, prefix)
    if existing:
        raise FileExistsError(
            f"{prefix} already contains {len(existing)} objects. "
            f"Released versions are immutable — cut a new version instead."
        )
