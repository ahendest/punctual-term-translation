# Punctual term translation

This is the terminology part of the Risalero workshop. It finds the right way to keep a
religious or technical term of an Islamic book in another language, and it waits for your
approval before any book uses it.

## What it does for you

Some words lose their meaning when they are translated into a general word: *namaz* is not just
"prayer", *nefs* is not just "self". For such a term the book prints:

> the original term (its approved translation)¹
>
> ¹ a short, reliable note with the Arabic spelling, only at the first use in the book

Later in the book the term is followed by its translation without parentheses. You can also
decide that a term has no note, no translation, or no original form, or that later uses keep
the original alone; the book follows that decision.

## What you supply

The translation part of the workshop
([agentic-translate](https://github.com/ahendest/agentic-translate)) gives you a list of terms
that need a decision, each with its place in the book, for example:

```text
namaz (sources/my-book/segments/004-chapter.md:12)
```

Open an agent in this folder and paste the list.

## What you approve

For each new term the agent researches how the term is used in the target language, then
writes two proposals, A and B, each with its note. A second, independent agent compares them
with the book and picks A, B or neither.

Everything appears in [results/results.md](results/results.md): the paragraph from the book,
both proposals, their notes and the reviewer's choice. Read it, then tell the agent exactly
which wording you approve, for example "I approve proposal A as written". You approve in the
conversation; the agent records it. Your choice is final, also when the reviewer picked the
other one. To rewrite a note, send only its
explanation; the term and its Arabic spelling stay at its start. Only your explicit
approval publishes a term. After approval the term is stored once and every book in that
language reuses it; its block disappears from `results/results.md`.

To change an approved term later, ask the agent to reconsider it. The same research, review
and approval steps apply.

## Reference books

The research can use the Kavramlar Lugatı EPUB. Books are not part of this repository: place
your own copy under `sources/originals/`. [sources/manifest.json](sources/manifest.json) names
the expected file and its checksum.

## More

- [AGENTS.md](AGENTS.md): the agents' instructions, commands and checks.
- [CHANGELOG.md](CHANGELOG.md) and [LICENSE](LICENSE) (MIT).
