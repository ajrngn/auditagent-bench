---
name: synthetic-authoring
description: Authors synthetic control scenarios and minimal pairs for AuditAgent Bench Task B, and the severity-gradient items periodic filings cannot supply. Use when writing or reviewing control design scenarios, building minimal pairs, setting gap_type or gradient_bearing, recording drafted_by, or deciding whether a scenario is realistic enough to release.
---

# Synthetic authoring

Task B is synthetic by design, and synthetic items also carry the severity gradient that SEC filings cannot — disclosure rules compel material weaknesses only, so `deficiency` and `significant_deficiency` have to come from here or from Single Audit findings.

Synthetic items are the only contamination-free part of the benchmark. That makes them the reasoning control group, and it makes their quality load-bearing.

## Minimal pairs are the point

A minimal pair is two items sharing a `minimal_pair_id`: identical process narrative and control description except for **one deliberate change**. One is `pair_role: control`, the other `pair_role: variant`.

```
control:  ... invoices over $50,000 are approved by the controller, who does
          not have access to the vendor master file ...
variant:  ... invoices over $50,000 are approved by the controller, who also
          maintains the vendor master file ...
```

Same length, same register, same surrounding sentences. Only the segregation-of-duties fact moves.

Why this matters more than volume: a model that answers both halves correctly is reasoning about the control. One that flips based on surrounding language is pattern-matching on disclosure boilerplate. **No real filing can produce this** — you cannot get the counterfactual version of a company's actual control.

Rules:
- Change exactly one fact. Two changes make the result uninterpretable.
- Keep length within ~10% between halves. A length signal is a confound.
- Both halves get the same `drafted_by` and the same reviewer.
- Report per-pair consistency as a metric: the share of pairs where the model got both halves right. That number is more informative than raw Task B accuracy.

## Generate from structure, not from a blank prompt

Free-form generation clusters on whatever failure modes are salient to the drafting model — usually segregation of duties and management review, over and over. Drive it from a cross instead:

- **Process:** procure-to-pay, order-to-cash, financial close, payroll, inventory, treasury
- **Gap type:** `segregation_of_duties`, `precision`, `evidence`, `timeliness`, `management_review`, `access`
- **Severity:** `deficiency`, `significant_deficiency`, `material_weakness`
- **Entity size:** affects plausible compensating controls; a three-person finance team cannot segregate the way a large filer can

Enumerate the cells you want, then draft into them. Track coverage as a matrix and fill gaps deliberately. Uneven coverage is fine if it is *chosen*; uneven coverage you discovered afterward is a sampling artifact.

## Style must match real filings

Real Item 9A prose is hedged, bureaucratic, and repetitive. Synthetic scenarios come out crisp, well-organized, and unnaturally clear. A model may score well on one and badly on the other for purely stylistic reasons, which you would then misread as a reasoning difference.

Ground the drafting prompt on real extracted `icfr_text` excerpts for register. Read a handful of live Item 9A sections before authoring a batch. Match sentence length and hedging density; do not match specific facts, and never paraphrase a real filing closely enough to be derivative of it.

Task B inputs are `process_narrative` + `control_description`, not disclosure prose — so exact filing register matters less here than it does for any synthetic Task A or C item, where the model sees text that is supposed to look like a filing.

## Drafting conflict — disclose it

If a model drafts scenarios and that same model is evaluated on them, that is a conflict.

- Record `provenance.drafted_by` on every synthetic item: full pinned model identifier, or `human`.
- **Draft with a different model family than the headline evaluees**, where practical.
- Report Task B scores split by `drafted_by`. If items drafted by a vendor's model favour that vendor, that must be visible in the results table rather than buried in a methods note.
- Never leave `drafted_by` unset. An unattributed synthetic item cannot be audited for this bias.

## Provenance for synthetic items

```json
"provenance": {
  "origin": "synthetic",
  "jurisdiction": "XX",
  "regime": "none",
  "drafted_by": "<full pinned model id> | human"
}
```

`jurisdiction: XX` and `regime: none` are deliberate — a synthetic scenario has no real filer and was made under no regime. Do not label them `US` / `sox_404` to make the counts look tidier; that would misstate what the item is.

## The label rules still bind

Everything in `labeling-controls` applies. A synthetic item is an **`llm_draft` until a human reviews it**, and only the reviewer-triggered Apps Script path may write `llm_draft_human_verified`. Drafting a scenario and its label in the same pass does not make the label verified — the model that invented the gap is not evidence the gap is what it claims.

Minimal pairs make review cheaper: the reviewer checks one delta rather than reading two full scenarios. Present them side by side in the sheet, adjacent rows, same `minimal_pair_id`.

## Set gradient_bearing

Synthetic items get `label.gradient_bearing: true` — the author could have chosen any severity, so severity here is a real signal rather than an artifact of what disclosure rules compel. This is what makes Task A's severity score meaningful at all.
