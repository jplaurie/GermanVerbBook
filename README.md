# German Verb Reference

This repository contains a German grammar and verb-reference book developed
as part of my own German-learning journey. It brings together the rules,
patterns, and examples that I have found most useful, with a particular focus
on practical verb usage.

The book is an ongoing project. Corrections and constructive suggestions are
welcome.

All 600 verb tables are maintained as structured YAML rather than handwritten
LaTeX records. The grammar chapters and visual design remain in LaTeX because
prose and print layout are already expressed well there. The build pipeline is:

```text
verbs/verbs.yaml -> validation -> verbs/verb-list.tex -> GermanBook.pdf
```

`verbs/verb-list.tex` is generated. Edit `verbs/verbs.yaml`, then regenerate.

## Requirements

- Python 3
- PyYAML (`python-yaml` on Arch Linux)
- `latexmk` and the LaTeX packages used by `style/germanbook.sty`

## Build

```sh
make
```

This validates the YAML, regenerates `verbs/verb-list.tex` when necessary, and
builds `GermanBook.pdf`. Building in the project root is intentional: the two
`imakeidx` indexes then find their generated `.idx` files and apply
`style/germanbook.ist` during the LaTeX run.

Other useful commands are:

```sh
make generate  # regenerate verbs/verb-list.tex
make check     # validate YAML and check that generated LaTeX is current
make test      # run the catalogue tests
make clean     # remove LaTeX build products
```

The underlying generator commands are also available as
`python3 scripts/generate_verbs.py` and
`python3 scripts/generate_verbs.py --check`.

## Project layout

- `main.tex` — book assembly and ordering
- `grammar/` — grammar-reference chapters
- `verbs/verbs.yaml` — canonical source for all verb data
- `verbs/verb-list.tex` — generated LaTeX; do not edit directly
- `verbs/introductions/` — explanatory notes included in the verb reference
- `scripts/verb_data.py` — schema validation and LaTeX rendering
- `scripts/generate_verbs.py` — generator and generated-file check
- `style/germanbook.sty` — shared book and verb-table presentation
- `templates/new-verb.yaml` — starter record for adding a verb
- `tests/` — catalogue and generation regression tests

## Editing verb data

Copy `templates/new-verb.yaml` into the appropriate chapter and alphabetical
group in `verbs/verbs.yaml`, then edit the new record. The YAML retains the
book's chapter and alphabetical-section ordering. Each verb separates:

- identity and English meaning;
- grammatical classification, auxiliary selection, and visual case style;
- person-keyed present, preterite, and optional subjunctive forms;
- role-keyed imperative forms;
- structured perfect, future, and pluperfect constructions;
- prepositional patterns with explicit government;
- related separable compounds with an unformatted split marker.

`grammar.type` is a broad verb classification and uses five values: `regular`,
`irregular`, `mixed`, `modal`, and `variable`. Case government, reflexivity,
prefix behaviour, and register do not belong in this label; they are either
represented elsewhere in the record or left out of the compact heading.

The two explanatory callout boxes remain in `verbs/introductions/`, just as
the longer grammar prose remains in `grammar/`.

`scripts/import_existing_tex.py` records how the initial YAML data was
migrated from the former handwritten `verbs/verb-list.tex`. It is retained as
migration history and is not part of the normal editing workflow.
