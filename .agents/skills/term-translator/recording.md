# Record a term result

Read this when saving research. Run commands from punctual-term-translation.
Uppercase arguments are values from the current request.

```bash
python3 -B tools/terms.py show --run RUN_ID
python3 -B tools/terms.py submit --run RUN_ID --input /tmp/resolve.json
```

Submit validates the result, saves it in the run file and refreshes the run's block in
`results/results.md`. A new submit replaces the earlier result and clears its review. Keep
temporary payloads outside the repository.

```json
{
  "sense": "Meaning of the term in the located paragraph",
  "origin": {"verified": "Full verified source expression; inspected reference and locator"},
  "queries": ["Search actually performed"],
  "usage": [],
  "limitations": ["Specific limitation of the usage research"],
  "route": "compare",
  "reading_form": "Retained term in the target language's reading form",
  "arabic": "Complete Arabic expression, or null when the term has no Arabic origin",
  "note": null,
  "options": [
    {"label": "A", "translation": "sens", "footnote": "First-use footnote A", "paragraph": "Acest sens apare."},
    {"label": "B", "translation": "înțeles", "footnote": "First-use footnote B", "paragraph": "Acest înțeles apare."}
  ]
}
```

Replace every example value. All fields except `note` are required; extra fields are
rejected. Origin contains nonempty `verified` and/or `limitation` text. When `arabic` is set,
every footnote must contain it exactly. Keep usage evidence in usage; origin evidence alone
does not establish target-language usage. Queries must list real searches. Limitations can
be empty when none remain. Use `note` only when a term needs different renderings by
context; it guides translators and does not force one rendering. Apply the
[final check](SKILL.md#final-check) before submission and before presenting the selected
result for approval; structural validation does not verify meaning or Arabic completeness.

Each usage source has this shape:

```json
{
  "kind": "inspected",
  "title": "Source title",
  "author": null,
  "date": null,
  "url": "Source URL",
  "locator": null,
  "excerpt": "Exact inspected wording",
  "context": "What the passage means",
  "provenance": "How the source was inspected"
}
```

Use nonempty strings; only unknown author, date and locator can be null. Uninspected
results use `kind: search_lead` and do not prove usage. Empty usage requires an explicit
research limitation.

Use `route: attested` only for inspected usage of the same concept in the target language,
with option A alone. Every self-translated proposal uses `compare`, exactly A/B and
independent review. Both paragraphs must be identical after replacing their respective
translation with the same marker, and each paragraph must contain its translation. Include
necessary grammatical agreement in that expression. Record the reading form and translation
in their base form; translators inflect both as each sentence requires. The book prints the
term as `reading form¹ (translation)`; the comparison packet carries both paragraphs and both
footnotes.

The reviewer records only `A`, `B` or `none`. When a run is ready, its block in
`results/results.md` prints the approval command. `none` blocks approval of that term. On a
tool error, correct the cause before retrying.
