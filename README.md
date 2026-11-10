# Punctual term translation

This is the terminology part of the Risale translation workshop. It finds the right way to keep
a religious or technical term of an Islamic book in another language, and it waits for your
approval before any book uses it.

## What it does for you

A concept that your language names with a usual word is simply translated; you approve the
word once and every book uses it. Some concepts have no such word. For such a term the book
prints:

> the original term (its approved translation)¹
>
> ¹ a short, reliable note with the Arabic spelling, only at the first use in the book

Later in the book the term stands alone. You can also decide that a term has no note or no
translation; the book follows that decision.

## What you supply

The translation part of the workshop
([agentic-translate](https://github.com/ahendest/agentic-translate)) writes the terms that need
a decision into `results/requested-terms.md`, each with its place in the book, for example:

```text
TERM (sources/my-book/segments/004-chapter.md:12)
```

Open an agent in the workshop folder and tell it to start as the term translator; the
translation agent gives you the exact message to paste. It takes every
waiting term, continues with terms that arrive while it works, and stops when none is left.
If a session stops in the middle, a new session continues the same terms.

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
approval publishes a term. After approval the term is stored once and every book with the same
source and target language reuses it; its block disappears from `results/results.md`.

To change an approved term later, ask the agent to reconsider it. The same research, review
and approval steps apply.

## Reference books

The research can use the Kavramlar Lugatı EPUB. Books are not part of this repository: place
your own copy under `sources/originals/`. [sources/manifest.json](sources/manifest.json) names
the expected file and its checksum.

## More

- [AGENTS.md](AGENTS.md): the agents' instructions, commands and checks.
- [CHANGELOG.md](CHANGELOG.md) and [LICENSE](LICENSE) (MIT).
