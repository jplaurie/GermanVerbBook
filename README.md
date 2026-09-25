# German Verb Reference

This project is a reorganized, book-oriented edition of `verb_table_v6.tex`.
The legacy source is retained under `legacy/` for comparison.

## Build

```sh
latexmk -pdf -jobname=GermanBook main.tex
```

The result is `GermanBook.pdf`. Run `latexmk -C` to remove generated files.

## Project layout

- `main.tex` — book assembly and ordering
- `style/germanbook.sty` — the shared `\VerbTable` renderer
- `grammar/` — grammar-reference chapters
- `verbs/verb-list.tex` — the single canonical list of all verb data
- `templates/new-verb.tex` — starter entry for adding a verb
- `legacy/verb_table_v6.tex` — unchanged original source

## Adding a verb

Copy the entry in `templates/new-verb.tex` into the correct alphabetical
position in `verbs/verb-list.tex`, then fill in its fields. `\VerbTable` owns
the box, heading alignment, row labels, empty-section dashes and indexes, so
those features are not duplicated in individual entries. Leave `subjunctive`
empty when it is not being shown; use `---` for an imperative, preposition or
related-separable-verb section that has no forms to display.
