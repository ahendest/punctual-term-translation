# Changelog

## Unreleased

- A term without Latin letters or digits gets a stable hash ID; an ID that holds another
  original is refused and needs `--term-id`. Existing IDs are unchanged.
- `ask` reuses only an exact original; prefix-only matches return `candidates`
  (`--term-id` reuses one, `--new` starts research).
- `review` requires the packet `--digest`; a verdict on a changed proposal is rejected.
- A proposal records only what is shown or approved: `sense`, `route`, `reading_form`,
  `arabic`, optional `note` and the options. Research stays in the conversation; `origin`,
  `queries`, `usage` and `limitations` are no longer recorded.
- A run is no longer bound to a hash of its source file; the run's `book` and the paragraph ID
  are dropped. A reconsideration no longer keeps book placements: the shared store has none.
- The repository's own CI is removed; the workshop CI checks both areas at pinned commits.
- The first-use format is `term (equivalent)¹`.

## 0.1.0 (2026-10-25)

First public release.

- Term locations are `segment.md:line` in EPUB-prepared units. Nearby context is the heading
  section around the term; the page concept is removed.
- Works with the shared store schema 6 of agentic-translate.
- Reference books are no longer tracked; `sources/manifest.json` names them with checksums.
- MIT licence and CI.
