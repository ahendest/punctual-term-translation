# Record a term result

Read this when saving a proposal. Run commands from punctual-term-translation.
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
rejected. When `arabic` is set, every footnote must contain it exactly. Use `note` only when a
term needs different renderings by context; it guides translators and does not force one
rendering. Apply the [final check](SKILL.md#final-check) before submission and before
presenting the selected result for approval; structural validation does not verify meaning
or Arabic completeness.

Use `route: attested` only for verified established usage of the same concept in the target
language, with option A alone. Every self-translated proposal uses `compare`, exactly A/B and
independent review. Both paragraphs must be identical after replacing their respective
translation with the same marker, and each paragraph must contain its translation. Include
necessary grammatical agreement in that expression. Record the reading form and translation
in their base form; translators inflect both as each sentence requires. The book prints the
term as `reading form (translation)¹`, in Markdown `reading form (translation)[^TERM_ID]`; the
comparison packet carries both paragraphs and both footnotes.

The reviewer records only `A`, `B` or `none`. When a run is ready, its block in
`results/results.md` prints the approval command. `none` blocks approval of that term. On a
tool error, correct the cause before retrying.
