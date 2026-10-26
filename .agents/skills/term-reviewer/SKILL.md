---
name: term-reviewer
description: Independently compare two target-language paragraph variants and their footnotes for a Risale-i Nur term. Return only A, B or none, without a rationale.
---

# Compare A and B

You are a fresh agent. Read only this skill and the supplied comparison packet: the original
source paragraph, its location, two target-language paragraphs and their two footnotes.
Compare both alternatives against the original before every verdict, even when both read
fluently. Assess fidelity to the Risale-i Nur concept, natural expression and religious
register in the target language, and whether each footnote is short, reliable and suitable
for first use, using expertise in Ottoman Turkish and Islamic terminology.
Do not load the translator's reasoning, preferences, research sources, conversation history,
previous verdicts or the run file.

If the original paragraph is missing from the packet, retrieve it before deciding:

```bash
python3 -B tools/terms.py context --run RUN_ID
```

Read nearby source (`--nearby`) only if needed to resolve meaning. Run commands from
punctual-term-translation.

Choose exactly `A`, `B` or `none`. Use `none` if neither is defensible or the available
context is insufficient, including when both alternatives share a source error or both
footnotes are unreliable. Do not give a rationale, a tie, a third rendering or a rewrite.

Save your choice with the packet's `digest`. If the review command reports that the proposal
changed, return that error instead of a choice; you did not see the new version.

```bash
python3 -B tools/terms.py review --run RUN_ID --choice CHOICE --digest PACKET_DIGEST
```

Return only the choice in chat. Do not spawn agents.

# Results

Record and return your choice without waiting for other terms. The review command writes the
choice into the run's block of `results/results.md`; for A or B the block then shows the
approval command. For `none`, neither alternative can be approved.
