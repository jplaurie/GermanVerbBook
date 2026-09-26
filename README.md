# German Verb Reference

This repository contains a German grammar and verb-reference book developed
as part of my own German-learning journey. It brings together the rules,
patterns and examples that I have found most useful, with a particular focus
on practical verb usage.

The book is an ongoing project and will continue to evolve as I learn, revise
the material and improve its presentation. Corrections and constructive
suggestions are welcome.

All verb data is maintained in one canonical source file.

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

## Adding a verb

Copy the entry in `templates/new-verb.tex` into the correct alphabetical
position in `verbs/verb-list.tex`, then fill in its fields. `\VerbTable` owns
the box, heading alignment, row labels, empty-section dashes and indexes, so
those features are not duplicated in individual entries. Leave `subjunctive`
empty when it is not being shown; use `---` for an imperative, preposition or
related-separable-verb section that has no forms to display.

Do not add a separate full table for a separable compound whose base verb is
already present. Add it to that stem's `separable` field using `\relatedverb`,
for example:

```tex
& \relatedverb{ausstellen}{to issue / exhibit}{aus$|$stellen}
  & (to issue / exhibit)\\
```

The command keeps the compact compound in both indexes. A genuinely missing
base stem should receive a full `\VerbTable` entry first. The base table
supplies the compound's stem pattern, but its auxiliary may differ according
to meaning; the book's table-convention note explains this distinction.
