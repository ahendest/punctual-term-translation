# Punctual term translation

## Purpose

For a given term or list of terms, provide the equivalent in the project's target language to
be used in parentheses, a clear, short and reliable footnote, and the Arabic spelling of the
term inside that footnote, unless the shared store already holds them
(`agentic-translate/knowledge/knowledge.sqlite`). Translate only after a suitable context is
established.

Format returned for the book:

> the original term in the reading form of the target language¹ (the approved equivalent)
>
> ¹ footnote, used only at the first appearance in the book

A suitable context starts with understanding the term. The paragraph in which the term occurs
is the first context. If the term carries a technical meaning that is hard to express in the
target language, consult the references: <https://sorularlarisale.com/>,
<https://sorularlaislamiyet.com/>, <https://islamansiklopedisi.org.tr/>, the Kavramlar Lugatı
EPUB under `sources/originals/` when the user has placed it there (`sources/manifest.json`
names it; books are not tracked), and the dictionary in the shared store
(`knowledge.py lugat search`). Proposals and footnotes follow the skill's Voice section, in
harmony with the book's translation.

The target language comes from the project manifest of the source location. Never write
language-specific rules into tools, schemas or these instructions.

## Start

Start with [term-translator](.agents/skills/term-translator/SKILL.md) and its Voice section.
You perform the work in this conversation. Delegate only the independent comparison to
[term-reviewer](.agents/skills/term-reviewer/SKILL.md): a fresh agent of your own model,
started with that skill and the comparison packet, with no shared history.

## Always do

- Accept `term (source-segment.md:line)`. Use its exact paragraph and only the nearby
  context needed for meaning. The ask command extracts it; do not rediscover its location.
- Keep understanding, usage research and translation in this session.
- For new translations, record two A/B alternatives with their footnotes. The tool shows
  them in `results/results.md`; the user reads A, B, the reviewer's choice and the approval
  command there. Apply the translator skill's final check to the selected equivalent,
  complete Arabic expression and footnote before asking for approval.
- Use the configured shared SQLite file. Incoming terms are already checked; do not
  repeat approved-term discovery here.
- Read [recording.md](.agents/skills/term-translator/recording.md) when saving work. Record
  real evidence and limitations; keep temporary payloads outside the repository.

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
- Create another active database, edit a Voice section without a request, name a model or
  vendor in instructions, commit or publish without explicit authorization.

## Checks

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 -B tools/terms.py check
```
