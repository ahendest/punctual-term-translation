# Punctual term translation

## Purpose

For a given term or list of terms, provide the equivalent in the project's target language to
be used in parentheses, a clear, short and reliable footnote, and the Arabic spelling of the
term inside that footnote, unless the shared store already holds them
(`agentic-translate/knowledge/knowledge.sqlite`). Translate only after a suitable context is
established.

Format returned for the book:

> the original term in the reading form of the target language (the approved equivalent)¹
>
> ¹ footnote, used only at the first appearance in the book
>
> later appearances: the original term in the reading form, directly followed by the approved
> equivalent as an apposition

A record keeps only the parts the user approves; each missing part is a decision:

- no footnote: no note call;
- no equivalent: the original alone, with its note call at the first use;
- no reading form: the equivalent alone, translated by meaning;
- later use `original`: after the first use, the original alone;
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
