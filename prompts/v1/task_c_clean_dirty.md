# Task C — Clean/dirty discrimination (prompt v1)

> Template file. `{{disclosure_text}}` is the only substitution.
> Editing this file requires bumping the prompt version directory and re-running every model.
>
> **Design note:** the prompt must not signal that a deficiency is present. The headline metric is
> the false-positive rate on clean disclosures, so any leading language invalidates the measurement.
> Do not add "identify the weakness" phrasing.

---

Below is the "Controls and Procedures" section (Item 9A) of a public company's annual report on Form 10-K.

Determine whether management disclosed a **material weakness** in internal control over financial reporting. Many companies conclude that their controls are effective and disclose no weakness; that is a normal and expected outcome.

Answer based only on what the text states. Do not flag a weakness because the section discusses the framework used, the scope of management's assessment, inherent limitations of internal control, or changes in controls during the period — those appear in ordinary clean disclosures.

Respond with JSON only, no prose and no markdown fences:

```
{"is_deficient": true|false, "confidence": <0.0-1.0>, "rationale": "<one sentence>"}
```

## Item 9A

{{disclosure_text}}
