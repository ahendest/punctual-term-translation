# Punctual term translation

## Purpose

For a given term or list of terms, decide with the user how the book writes it, unless the
shared store already holds it
(`agentic-translate/knowledge/SOURCE_LANG.sqlite`, the store of the book's source language). Translate only after a suitable context is
established.

A concept that the target language names with a usual word is translated: record that word
as the equivalent, without a reading form. Keep the original only when the target language has
no usual word for the concept, or when the user wants the term kept. Format of a kept term:

> the original term in the reading form of the target language (the approved equivalent)¹
>
> ¹ footnote with the Arabic spelling of the term, used only at the first appearance in the book
>
> later appearances: the original term in the reading form, alone

A record keeps only the parts the user approves; each missing part is a decision:

- no reading form: the equivalent alone, never the original;
- no equivalent: the original alone, with its note call at the first use;
- no footnote: no note call;
- a note alone: guidance for the book translator, who translates by meaning.

The source and target languages come from the project manifest of the source location; an
approved record serves only books of its source language.

## Start

Start with [term-translator](.agents/skills/term-translator/SKILL.md).

## Always do

- Run `python3 -B tools/requests.py next`. It prints `new: N` or `resume: N`, then one
  `term (source-segment.md:line)` request per line; work on those lines.
- A request line may end with `user: DECISION`, the user's own treatment of the term; record
  it with route `directed` and confirm its exact wording with the user before approval.
- A request line may end with `translated: WORD`: the book translator already wrote this usual
  word and its unit does not wait. Judge WORD like any proposal. When the approved wording
  differs from WORD, name the term, WORD and the approved wording in the message that returns
  the work to the translation coordinator.
- Record every request: approved wording, or a note alone when it needs no wording. Then run
  `python3 -B tools/requests.py next --finished`; it refuses while runs are open. Stop on
  `new: 0`; otherwise work on the printed lines.

## Ask first

- Obtain explicit human approval of exact new equivalents and footnotes before publication.
  A reviewer choice or permission to change the system is not that approval.
- Ask about missing source identity or meaning only after using the named paragraph and
  necessary surroundings.

## Never do

- Spawn another term-translator. Delegate only review.
- Skip review or submit one candidate for a self-created translation.
- Give the reviewer your reasoning, preference, research sources or conversation history.
- Fabricate evidence, infer approval from historical records, or silently change approved text.
- Edit a Voice section without a request.

## Checks

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 -B tools/terms.py check
```
