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
  "reading_form": "Retained term in the target language's reading form, or null",
  "arabic": "Complete Arabic expression, or null when the term has no Arabic origin",
  "note": null,
  "later_use": "equivalent",
  "options": [
    {"label": "A", "translation": "sens", "footnote": "First-use footnote A", "paragraph": "Acest sens apare."},
    {"label": "B", "translation": "înțeles", "footnote": "First-use footnote B", "paragraph": "Acest înțeles apare."}
  ]
}
```

Replace every example value. `note` and `later_use` are optional; extra fields are rejected.
When `arabic` is set, every footnote must contain it exactly. Null `reading_form`,
`translation`, `footnote` or `paragraph` and `later_use: original` record the forms listed in
[AGENTS.md](../../../AGENTS.md#purpose); use them as the user decides. A note guides
translators by context and links a plural or spelling variant to its record; a record may
hold only a note. Give B the same footnote as A when they
share it; `results/results.md` then shows it once. Apply the [final check](SKILL.md#final-check) before submission and before
presenting the selected result for approval; structural validation does not verify meaning
or Arabic completeness.

Use `route: attested` for verified established usage of the same concept in the target
language, and `route: directed` for a treatment the user dictates; both have option A alone and
no review. Every self-translated proposal uses `compare`, exactly A/B and independent review. Both paragraphs must be identical after replacing their respective
translation with the same marker, and each paragraph must contain its translation. Include
necessary grammatical agreement in that expression. Record the reading form and translation
in their base form; translators inflect both as each sentence requires. The book prints the
term at its first use as `reading form (translation)¹`, in Markdown
`reading form (translation)[^TERM_ID]`, and later as `reading form translation`; the
comparison packet carries both paragraphs and both footnotes.

The reviewer records only `A`, `B` or `none`. `none` blocks approval of that term until the
user dictates a wording. On a
tool error, correct the cause before retrying.
