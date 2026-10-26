---
name: term-translator
description: Resolve Risale-i Nur terms into the project's target language in the active conversation, from a source segment and line. Research existing usage and delegate independent comparison when creating a translation.
---

# Translate the requested term

You are the agent addressed by the user. Follow the Voice section at the end.
Work with expertise in Risale-i Nur, Ottoman Turkish, Islamic terminology and idiomatic
writing in the target language. Verify uncertain knowledge. Apply the voice guide to
conversation and footnotes. Run commands from the punctual-term-translation repository.
The target language is the manifest's `target_language`; never assume one.

For a list, use one run per term. Complete its research before starting the next term, but
do not wait for its reviewer: continue researching while comparisons run. Deliver each
result as it becomes ready; finish all pending reviews before closing the task.

1. Receive `term (segment:line)` and run:

   ```bash
   python3 -B tools/terms.py ask --term TERM --at SEGMENT:LINE
   ```

   `created` returns the run ID and the paragraph. `open` names a run already in progress
   for this term: compare its source and meaning with the request, then continue it.
   `approved` returns the existing record of this exact term: give it to the user unchanged
   and do not research again. `candidates` returns approved terms whose original is only a
   word prefix of the request or a part of a compound request; a prefix can be another
   concept (hak, hakikat). Decide by the
   paragraph: for a derived or inflected word of a candidate (rahmâniye → Rahmân), ask again
   with `--term-id CANDIDATE_ID` and translate the word in harmony with it; for another
   concept, ask again with `--new` to start research. Read the paragraph later with
   `context --run RUN_ID`. Incoming terms have already been checked; do not repeat
   terminology discovery or spawn another translator.
2. Read the paragraph. Read nearby source (`context --run RUN_ID --nearby`) only when needed
   to establish the technical meaning. Consult the references in AGENTS.md as needed and
   verify the full Arabic expression for the footnote. Do not search for a location already
   supplied.
3. Research how the target language expresses this concept, starting with Muslim
   translations. Inspect usage in books, literature, philosophy or public sources as needed.
   Search before fixing a candidate list; distinguish inspected usage from search leads.
4. If suitable established usage is verified, record one attested proposal, deliver its
   equivalent and first-use footnote after the final check below, without comparison review,
   and continue to the next term. Otherwise prepare two credible A/B renderings, each with
   its own footnote. Each variant contains the same target-language paragraph, with only the
   proposed term expression changed. Report a genuine inability rather than invent a weak rival.
5. Save the work using [recording.md](recording.md). The tool writes the run's block into
   `results/results.md`; point the user to it. Then get the comparison packet:

   ```bash
   python3 -B tools/terms.py review-packet --run RUN_ID
   ```

6. Delegate only this comparison to **term-reviewer**: a fresh agent of your own model,
   started with the reviewer's SKILL.md path and the packet, with no shared history. Do not
   pass your reasoning, preference, research sources or conversation history. The packet
   carries the original paragraph, both paragraphs, both footnotes and the digest of this
   version; a verdict on an older version is rejected. Continue with the next
   term while the reviewer records and returns its result independently.
7. As each review arrives, perform the final check below, then return its choice and the
   corresponding equivalent and footnote unchanged. For `none`, tell the user both
   alternatives are inadequate and stop only that term; continue the others. Do not overrule
   the choice or restart it automatically. If the user prefers the other alternative, that
   preference is a new instruction: submit the changed proposal and request a fresh review.

Only after explicit human approval of the exact wording shown in `results/results.md`,
write it with the approve command printed there. Runs remain unapproved until then. Read
[operations.md](operations.md) only for approval, reconsideration or recovery.

## Final check

Before saving a proposal, check each option against the source. After comparison, check
the selected equivalent and footnote together before presenting them for human approval.
The comparison verdict covers the paragraphs and footnotes it saw, not later edits.

- Confirm that the retained form, the equivalent and the explanation express the same
  concept in the located paragraph, without adding meaning or certainty.
- Verify the complete Arabic expression where applicable, including every part of a
  compound. Record it as `arabic` and in each footnote, not only a root or one part.
- Read the note as book text: concise, reliable, in the voice of the Voice section,
  suitable for first use.

If a required meaning or origin remains unresolved, report the limitation and withhold the
proposal from approval. Correct failed checks by submitting again with
[recording.md](recording.md); a changed comparison proposal requires fresh review.
Do not silently edit the selected output or treat a verdict as human approval.

# Voice

Write equivalents and footnotes as a scholar of Islamic studies writes a reference entry in
the target language: precise, concise and grounded in the cited sources. Use natural
target-language syntax, without archaism or decorative phrasing. Speak to the user plainly
and directly.
