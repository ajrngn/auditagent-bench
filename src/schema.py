"""Schema validation and the benchmark release gate.

`04_build_benchmark` must not write a version that fails any check here.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"

# Provenance values a released item may carry. 'llm_draft' is deliberately
# absent: an unreviewed label never ships.
RELEASABLE_LABEL_SOURCES = {"disclosure", "human", "llm_draft_human_verified"}


def load_validator(name: str) -> Draft202012Validator:
    """Load a validator by schema stem, e.g. 'benchmark_item'."""
    schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_records(records: list[dict], schema_name: str) -> list[str]:
    """Return one error string per invalid record. Empty list means all valid."""
    validator = load_validator(schema_name)
    errors = []
    for i, record in enumerate(records):
        ident = record.get("item_id") or record.get("accession_number") or f"index {i}"
        for err in validator.iter_errors(record):
            errors.append(f"{ident}: {'/'.join(str(p) for p in err.path)}: {err.message}")
    return errors


def release_gate(items: list[dict]) -> tuple[bool, list[str]]:
    """Run every pre-release check. Returns (passed, report lines).

    Report lines are printed whether the gate passes or fails — a release
    records what was measured, not that it succeeded.
    """
    report: list[str] = []
    failures: list[str] = []

    def check(label: str, ok: bool, detail: str) -> None:
        report.append(f"[{'PASS' if ok else 'FAIL'}] {label}: {detail}")
        if not ok:
            failures.append(label)

    schema_errors = validate_records(items, "benchmark_item")
    check("schema", not schema_errors, f"{len(schema_errors)} errors" +
          (f" (first: {schema_errors[0]})" if schema_errors else ""))

    sources = Counter(i.get("label_source") for i in items)
    unreleasable = sum(n for s, n in sources.items() if s not in RELEASABLE_LABEL_SOURCES)
    check("label_source", unreleasable == 0,
          f"{unreleasable} unreleasable; " + ", ".join(f"{s}={n}" for s, n in sources.items()))

    ids = Counter(i.get("item_id") for i in items)
    dupe_ids = [k for k, n in ids.items() if n > 1]
    check("unique_item_id", not dupe_ids, f"{len(dupe_ids)} duplicates")

    by_task_accession: Counter = Counter()
    for i in items:
        acc = i.get("provenance", {}).get("accession_number")
        if acc:
            by_task_accession[(i["task"], acc)] += 1
    dupe_acc = [k for k, n in by_task_accession.items() if n > 1]
    check("unique_accession_per_task", not dupe_acc, f"{len(dupe_acc)} duplicates")

    known_ids = set(ids)
    orphans = [
        i["item_id"] for i in items
        if i.get("paraphrased") and i.get("paraphrase_of") not in known_ids
    ]
    check("paraphrase_twins", not orphans, f"{len(orphans)} orphaned")

    task_c = [i for i in items if i.get("task") == "C"]
    deficient = sum(1 for i in task_c if i.get("label", {}).get("is_deficient"))
    clean = len(task_c) - deficient
    balanced = bool(task_c) and 0.35 <= (clean / len(task_c)) <= 0.65
    check("task_c_balance", balanced, f"{clean} clean / {deficient} deficient")

    # A clean label means nobody disclosed a weakness. When a later 4.02 8-K or
    # subsequent-period material weakness contradicts that, the label is known
    # to be wrong — and a model correctly flagging it would be scored as a
    # false positive, inflating the headline metric.
    restated = [i["item_id"] for i in task_c
                if i.get("clean_confidence") == "excluded_restated"]
    check("no_restated_clean_items", not restated, f"{len(restated)} present")

    clean_items = [i for i in task_c if not i.get("label", {}).get("is_deficient")]
    unrated = [i["item_id"] for i in clean_items if not i.get("clean_confidence")]
    check("clean_confidence_set", not unrated, f"{len(unrated)} clean items unrated")

    attested = sum(1 for i in clean_items if i.get("clean_confidence") == "attested")
    check("attested_subset_viable", attested >= 30,
          f"{attested} attested clean items (headline FP rate is computed on these)")

    # Severity is only meaningful where the source could have expressed
    # something other than material_weakness.
    with_severity = [i for i in items if i.get("label", {}).get("severity")]
    gradient = [i for i in with_severity if i.get("label", {}).get("gradient_bearing")]
    mislabelled = [
        i["item_id"] for i in with_severity
        if i.get("label", {}).get("gradient_bearing")
        and i.get("provenance", {}).get("origin") == "sec_periodic"
    ]
    check("gradient_bearing_sources", not mislabelled,
          f"{len(mislabelled)} sec_periodic items claim a severity gradient")

    report.append("")
    report.append(f"Total items: {len(items)}")
    for task, n in sorted(Counter(i.get("task") for i in items).items()):
        report.append(f"  Task {task}: {n}")

    report.append("")
    report.append("Provenance:")
    for origin, n in sorted(Counter(
            i.get("provenance", {}).get("origin") for i in items).items()):
        report.append(f"  {origin}: {n}")
    for key in ("jurisdiction", "regime"):
        counts = Counter(i.get("provenance", {}).get(key) for i in items)
        report.append(f"  {key}: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    report.append("")
    report.append(f"Severity labels: {len(with_severity)} "
                  f"({len(gradient)} gradient-bearing, scored; "
                  f"{len(with_severity) - len(gradient)} not scored)")
    report.append(f"Clean confidence: " + ", ".join(
        f"{k}={v}" for k, v in sorted(
            Counter(i.get("clean_confidence") for i in clean_items).items())))

    return not failures, report
