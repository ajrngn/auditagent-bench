# Task A — Deficiency classification (prompt v1)

> Template file. `{{disclosure_text}}` is the only substitution.
> Editing this file requires bumping the prompt version directory and re-running every model.
>
> **Design note:** COSO component is the primary label, not severity. Public disclosure
> rules compel reporting of material weaknesses only, so severity from periodic filings is
> near-degenerate. The model is still asked for severity — it is scored only on
> `gradient_bearing` items (Single Audit findings and synthetic scenarios), where the
> source could have expressed something other than a material weakness.

---

You are evaluating a deficiency in internal control over financial reporting.

Read the description below and determine two things:

1. **COSO component** — which component of the COSO 2013 Internal Control–Integrated Framework the deficiency most directly implicates:
   - `control_environment`
   - `risk_assessment`
   - `control_activities`
   - `information_and_communication`
   - `monitoring_activities`

2. **Severity** — one of:
   - `deficiency` — a control does not allow management or employees to prevent or detect misstatements on a timely basis
   - `significant_deficiency` — less severe than a material weakness, yet important enough to merit attention by those responsible for oversight of financial reporting
   - `material_weakness` — a reasonable possibility that a material misstatement of the financial statements will not be prevented or detected on a timely basis

Base your answer only on the text provided. Do not infer facts about the entity from outside knowledge, and do not assume a severity from the fact that the deficiency was disclosed publicly.

Respond with JSON only, no prose and no markdown fences:

```
{"coso_component": "<one of the five values>", "severity": "<one of the three values>", "rationale": "<one sentence>"}
```

## Deficiency

{{disclosure_text}}
