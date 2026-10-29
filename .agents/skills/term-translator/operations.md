# Approval, reconsideration and recovery

Read only the section needed for the current operation. Run commands from
punctual-term-translation.

## Input routing

The input is `term (source-segment.md:line)`, with a one-based source line. The ask command
extracts the paragraph and reads the target language from the project manifest that owns the
segment. Use `--project PROJECT_JSON` only if the manifest cannot be resolved uniquely. Use
`--term-id TERM_ID` for a second meaning of an existing spelling, with a distinct ID, or to
reuse a `candidates` record that the paragraph shows is the same concept. Use `--new` when
the candidates are other concepts. A derived ID that already holds another source form is
refused; choose an explicit `--term-id`. Do not run terminology discovery here.

## Approval

The user approves in the conversation; you run the commands. `show` returns
`approval_digests`: `default` for the reviewer's choice or the single option, and one per
label. An approve digest covers the whole proposal; the review packet digest covers only
what the reviewer saw. Save the user's words for this term in a file outside the repository.
For the option the reviewer did not choose, pass `--choice LABEL` with that label's digest;
the user's choice is final. For a user-edited footnote, wording or treatment, submit it with
route `directed` first.

```bash
python3 -B tools/terms.py show --run RUN_ID
python3 -B tools/terms.py approve --run RUN_ID --digest DIGEST --user-text-file APPROVAL_FILE --dry-run
python3 -B tools/terms.py approve --run RUN_ID --digest DIGEST --user-text-file APPROVAL_FILE
python3 -B tools/terms.py approved --id TERM_ID
```

Only explicit human approval of exact equivalents and footnotes authorizes approval. Use the
real approval message and the current digest. Reviewer choice and permission to change the
system are not linguistic approval. Changed wording needs a new submit, a fresh comparison
when required, and approval of that wording.

Approve refuses a digest or a visible block that differs from the stored proposal. It writes
the term and the approval text in one transaction, deletes the run file and removes the run's
block from the canvas. The dry run writes nothing.

## Reconsideration

Only when the user asks to revise an approved term:

```bash
python3 -B tools/terms.py ask --term TERM --at SEGMENT:LINE --reconsider
```

The run follows the normal research, comparison and approval steps. Its approval replaces the
wording.

## Recovery

```bash
python3 -B tools/terms.py list
python3 -B tools/terms.py show --run RUN_ID
python3 -B tools/terms.py canvas --run RUN_ID
python3 -B tools/terms.py check
```

List shows open runs and their status. Canvas rebuilds a run's block. Check verifies the
shared store's structure, not research quality. Discard a run only on explicit user request.

```bash
python3 -B tools/terms.py discard --run RUN_ID
```
