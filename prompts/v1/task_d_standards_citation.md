# Task D — Standards citation (prompt v1)

> Template file. `{{disclosure_text}}` is the only substitution.
> Editing this file requires bumping the prompt version directory and re-running every model.

---

Below is a described internal control deficiency. Identify the authoritative reference that most directly governs it.

Cite **one** of:

- A COSO 2013 principle, as `COSO Principle N` (1–17)
- A PCAOB standard section, as `AS 2201.NN`

Give the identifier only. Do not quote or paraphrase the text of the framework or standard. If no single reference clearly applies, return `null` rather than selecting the closest available option.

Respond with JSON only, no prose and no markdown fences:

```
{"citation": "<identifier or null>", "coso_component": "<one of the five components>", "rationale": "<one sentence>"}
```

## Deficiency

{{disclosure_text}}
