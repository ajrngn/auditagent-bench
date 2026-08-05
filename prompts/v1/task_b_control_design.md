# Task B — Control design evaluation (prompt v1)

> Template file. Substitutions: `{{process_narrative}}`, `{{control_description}}`.
> Editing this file requires bumping the prompt version directory and re-running every model.

---

You are evaluating whether an internal control is **designed** effectively. Judge design only — assume the control operates exactly as described. Do not assess operating effectiveness.

A control is designed effectively if, operating as described, it would prevent or detect on a timely basis the misstatement the process is exposed to.

If it is not designed effectively, identify the single most significant gap:

- `segregation_of_duties` — one person can both initiate and approve, or perform and review
- `precision` — the control operates at a level too coarse to catch a material misstatement
- `evidence` — performance leaves no reviewable trace
- `timeliness` — the control occurs too late to prevent or detect on a timely basis
- `management_review` — a review control without defined criteria, thresholds, or follow-up on exceptions
- `access` — inappropriate system access undermines the control

Respond with JSON only, no prose and no markdown fences:

```
{"designed_effectively": true|false, "gap_type": "<one of the six values, or null if designed effectively>", "rationale": "<one sentence>"}
```

## Process narrative

{{process_narrative}}

## Control description

{{control_description}}
