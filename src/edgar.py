"""SEC EDGAR access with the rate limit and User-Agent policy applied in one place.

SEC blocks IPs that exceed roughly 10 requests/second or that send requests
without a descriptive User-Agent containing a real contact address. Both rules
are enforced here so no caller can forget them.
"""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Iterator

import requests

# SEC requires a descriptive User-Agent with a working contact address.
# Requests without one receive 403.
USER_AGENT = "AuditAgent Bench (ajrngn@gmail.com)"

# SEC's published ceiling is 10 requests/second. 8 leaves headroom for the
# retry path so a burst of retries cannot push the process over the limit.
MAX_REQUESTS_PER_SECOND = 8.0

FULL_TEXT_SEARCH = "https://efts.sec.gov/LATEST/search-index"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}"

_lock = threading.Lock()
_last_request_at = 0.0


def _throttle() -> None:
    global _last_request_at
    min_interval = 1.0 / MAX_REQUESTS_PER_SECOND
    with _lock:
        elapsed = time.monotonic() - _last_request_at
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        _last_request_at = time.monotonic()


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})
    return s


_session = session()


def get(url: str, *, params: dict | None = None, max_retries: int = 3) -> requests.Response:
    """Throttled GET with backoff on 429 and 5xx.

    Retries only transient failures. A 403 means the User-Agent was rejected or
    the IP is blocked — retrying makes that worse, so it raises immediately.
    """
    for attempt in range(max_retries):
        _throttle()
        resp = _session.get(url, params=params, timeout=30)

        if resp.status_code == 403:
            raise PermissionError(
                f"SEC returned 403 for {url}. Check the User-Agent header "
                f"({USER_AGENT!r}) or wait out an IP block."
            )
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt == max_retries - 1:
                resp.raise_for_status()
            # Backoff doubles each attempt: 2s, 4s. Short enough to finish a
            # long pull, long enough for SEC's limiter to reset.
            time.sleep(2 ** (attempt + 1))
            continue

        resp.raise_for_status()
        return resp

    raise RuntimeError(f"unreachable: retries exhausted for {url}")


def full_text_search(
    query: str,
    *,
    forms: str = "10-K",
    date_from: str | None = None,
    date_to: str | None = None,
    page_size: int = 100,
) -> Iterator[dict]:
    """Page through EDGAR full-text search hits.

    Backs the UI at sec.gov/edgar/search. Undocumented as a public API, so the
    response shape can change without notice — validate hits before relying on
    them, and record the query in the run manifest for reproducibility.
    Coverage starts at 2001.
    """
    offset = 0
    while True:
        params: dict[str, Any] = {"q": query, "forms": forms, "from": offset, "size": page_size}
        if date_from:
            params["startdt"] = date_from
        if date_to:
            params["enddt"] = date_to

        hits = get(FULL_TEXT_SEARCH, params=params).json().get("hits", {}).get("hits", [])
        if not hits:
            return
        yield from hits

        offset += len(hits)
        # EDGAR full-text search refuses to page past 10000 results.
        if len(hits) < page_size or offset >= 10_000:
            return


def hit_to_record(hit: dict) -> dict:
    """Map a full-text search hit to the fields the pipeline needs.

    The hit `_id` is "<accession>:<filename>", which names the exact document
    that matched — more reliable than scanning the filing index for a likely
    primary document.

    Note `root_forms` is a list and describes the *base* form: a 10-K/A
    amendment has root_forms ["10-K"]. Use `form` for the actual type, and
    filter amendments explicitly if the sample should exclude them.
    """
    src = hit["_source"]
    accession_raw, _, filename = hit["_id"].partition(":")
    accession = normalize_accession(src.get("adsh") or accession_raw)
    cik = str(src["ciks"][0]).lstrip("0")
    root_forms = src.get("root_forms") or []

    return {
        "accession_number": accession,
        "cik": cik,
        "company_name": src["display_names"][0],
        "filing_date": src["file_date"],
        "form_type": src.get("form") or (root_forms[0] if root_forms else "UNKNOWN"),
        "root_form": root_forms[0] if root_forms else "UNKNOWN",
        "source_url": document_url(cik, accession, filename) if filename else None,
    }


def submissions(cik: str | int) -> dict:
    """Filing history for a CIK, including the recent-filings index."""
    return get(SUBMISSIONS.format(cik=int(cik))).json()


def normalize_accession(accession: str) -> str:
    """Canonical dashed form: 0000320193-23-000106."""
    digits = re.sub(r"\D", "", accession)
    if len(digits) != 18:
        raise ValueError(f"accession number must have 18 digits, got {accession!r}")
    return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"


def document_url(cik: str | int, accession: str, filename: str) -> str:
    nodash = re.sub(r"\D", "", accession)
    return f"{ARCHIVES.format(cik=int(cik), accession_nodash=nodash)}/{filename}"


def primary_document(cik: str | int, accession: str) -> str:
    """URL of the filing's primary document, resolved from its index JSON."""
    nodash = re.sub(r"\D", "", accession)
    base = ARCHIVES.format(cik=int(cik), accession_nodash=nodash)
    items = get(f"{base}/index.json").json()["directory"]["item"]

    for item in items:
        name = item["name"]
        if name.endswith((".htm", ".html")) and not name.endswith("-index.htm"):
            return f"{base}/{name}"

    raise LookupError(f"no primary HTML document found for {accession}")
