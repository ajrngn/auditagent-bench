"""Model-output parsing and Item 9A extraction.

Two rules drive this module:

- A response that will not parse is recorded as a parse failure, never salvaged
  by pattern-matching an answer out of prose. A salvaged answer is a different
  measurement than a returned answer.
- An Item 9A span that cannot be located is rejected, never approximated. A
  truncated or whole-document fallback silently degrades the corpus.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup

_FENCE = re.compile(r"^\s*```(?:json)?\s*\n(.*?)\n?\s*```\s*$", re.DOTALL)


def strip_fences(text: str) -> str:
    """Remove a wrapping markdown code fence. Models add them regardless of instructions."""
    match = _FENCE.match(text)
    return match.group(1) if match else text.strip()


@dataclass
class ParseResult:
    ok: bool
    value: dict | None
    error: str | None
    raw: str


def parse_json_response(text: str, required_keys: set[str] | None = None) -> ParseResult:
    """Parse a model response into a dict.

    An unexpected key set counts as a parse failure, not as a wrong answer —
    scoring a response the model did not structure as asked measures the wrong
    thing.
    """
    candidate = strip_fences(text)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return ParseResult(False, None, f"json_decode_error: {exc}", text)

    if not isinstance(value, dict):
        return ParseResult(False, None, f"expected object, got {type(value).__name__}", text)

    if required_keys:
        missing = required_keys - value.keys()
        if missing:
            return ParseResult(False, None, f"missing_keys: {sorted(missing)}", text)

    return ParseResult(True, value, None, text)


# --- Item 9A extraction -------------------------------------------------------

# Filers write "ITEM 9A.", "Item 9A(T)", and variants separated by non-breaking
# spaces. Match the number and optional (T) suffix, tolerate any separator.
_ITEM_9A = re.compile(r"item\s*9A\s*\(?T?\)?\s*[.\-—:]?", re.IGNORECASE)
_NEXT_ITEM = re.compile(r"item\s*9B\s*[.\-—:]?|item\s*10\s*[.\-—:]?", re.IGNORECASE)

# Below this length the match is a table-of-contents entry or a cross-reference,
# not the section itself.
MIN_ITEM_9A_CHARS = 500


class ExtractionFailure(Exception):
    """Item 9A could not be located. Caller records the reason; it does not guess."""


def filing_text(html: str) -> str:
    """Visible text of a filing, with scripts, styles, and XBRL headers removed."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    for tag in soup.find_all(re.compile(r"^ix:header$", re.IGNORECASE)):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return re.sub(r"[   ]", " ", text)


def extract_item_9a(html: str) -> str:
    """Extract the Item 9A span from filing HTML.

    Raises ExtractionFailure rather than returning a partial or fallback span.
    The caller writes the failure and its reason to an extraction-failure list.
    """
    text = filing_text(html)

    starts = [m.end() for m in _ITEM_9A.finditer(text)]
    if not starts:
        raise ExtractionFailure("item_9a_heading_not_found")

    # The last occurrence is the section; earlier ones are the table of contents.
    for start in reversed(starts):
        next_item = _NEXT_ITEM.search(text, start)
        if not next_item:
            continue
        span = text[start : next_item.start()].strip()
        if len(span) >= MIN_ITEM_9A_CHARS:
            return re.sub(r"\n{3,}", "\n\n", span)

    raise ExtractionFailure(
        f"no_span_over_{MIN_ITEM_9A_CHARS}_chars_before_next_item"
    )
