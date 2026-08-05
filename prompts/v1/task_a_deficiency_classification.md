# Task A — Deficiency classification (prompt v1)

> Template file. `{{disclosure_text}}` is the only substitution.
> Editing this file requires bumping the prompt version directory and re-running every model.

---

You are evaluating an internal control deficiency disclosed by a public company under Section 404 of the Sarbanes-Oxley Act.

Read the disclosure below and determine two things:

1. **Severity** — one of:
   - `deficiency` — a control does not allow management or employees to prevent or detect misstatements on a timely basis
   - `significant_deficiency` — less severe than a material weakness, yet important enough to merit attention by those responsible for oversight of financial reporting
   - `material_weakness` — a reasonable possibility that a material misstatement of the financial statements will not be prevented or detected on a timely basis

2. **COSO component** — the 2013 framework component most directly implicated: `control_environment`, `risk_assessment`, `control_activities`, `information_and_communication`, or `monitoring_activities`.

Base your answer only on the text provided. Do not infer facts about the company from outside knowledge.

Respond with JSON only, no prose and no markdown fences:

```
{"severity": "<one of the three values>", "coso_component": "<one of the five values>", "rationale": "<one sentence>"}
```

## Disclosure

{{disclosure_text}}
