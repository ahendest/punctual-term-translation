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
  "paragraph": "Target-language paragraph with {{TERM}} in place of the equivalent",
  "options": [
    {"label": "A", "translation": "equivalent A", "footnote": "First-use footnote A"},
    {"label": "B", "translation": "equivalent B", "footnote": "First-use footnote B"}
  ]
}
```

Replace every example value. `note` and `later_use` are optional; extra fields are rejected.
When `arabic` is set, every footnote must contain it exactly. Null `reading_form`,
`translation`, `footnote` or `paragraph` and `later_use: original` record the forms listed in
[AGENTS.md](../../../AGENTS.md#purpose); use them as the user decides. A note guides
translators by context and links a plural or spelling variant to its record; a record may
hold only a note. Give B the same footnote as A when they
share it; `results/results.md` then shows it once. Apply the [final check](SKILL.md#final-check); structural validation does not verify meaning
or Arabic completeness.

Use `route: attested` for verified established usage of the same concept in the target
language, and `route: directed` for a treatment the user dictates; both have option A alone and
no review. Every self-translated proposal uses `compare`. Write the target-language paragraph
once, with `{{TERM}}` at each place of the translation; the tool fills it in for A and B. Do
not write a paragraph per option. Include necessary grammatical agreement in the translation.
For `attested` and `directed`, give the paragraph in option A instead, or null. Record the reading form and translation
in their base form; translators inflect both as each sentence requires.

The reviewer records only `A`, `B` or `none`. `none` blocks approval of that term until the
user dictates a wording. On a
tool error, correct the cause before retrying.
