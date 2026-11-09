# German Verb Reference

This repository contains a German grammar and verb-reference book developed
as part of my own German-learning journey. It brings together the rules,
patterns, and examples that I have found most useful, with a particular focus
on practical verb usage.

The book is an ongoing project. Corrections and constructive suggestions are
welcome.

All 635 verb tables are maintained as structured YAML records. The grammar chapters and visual design remain in LaTeX because
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
- `grammar/comparative-and-superlative.tex` — comparison rules, examples and
  60 common adjective forms; cross-references the existing declension tables
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

An optional `display_name` overrides the bold table heading while `lemma`
retains the unique entry name used for validation and indexing.

### Table colours

`grammar.style` records the common object-case patterns in the meanings shown:

| Style | Background | Pattern |
| --- | --- | --- |
| `acc` | Blue | Accusative object or reflexive pronoun |
| `dat` | Green | Dative object |
| `accdat` | Purple | Both cases, together or in different common meanings |
| `default` | Grey | No Akk/Dat object pattern highlighted in the usual meaning |
| `nom` | Pink | Nominative complement of the auxiliaries `sein` and `werden` |
| `modal` | Yellow | Modal-verb chapter |

Prepositional government does not determine the background. Count reflexive
pronouns: `sich erinnern` is `acc`, whereas `sich merken` is `accdat`
(`sich` in the dative plus an accusative thing remembered). Do not classify a
verb as `accdat` solely because a free beneficiary can be added: `etwas kaufen`
remains `acc` even though `jemandem etwas kaufen` is possible.

The printed `KONSTRUKTIONEN` block includes both bare object-case patterns and
prepositional uses; the data field remains named `prepositional_uses`.

Colours describe selected common patterns, not every sense or an obligation
to express an object in every sentence. Compact compounds do not inherit the
stem's case government. The printed legend is in
`verbs/introductions/table-convention.tex`; editorial decisions and references
are recorded in [docs/verb-case-colours.md](docs/verb-case-colours.md).

The two explanatory callout boxes remain in `verbs/introductions/`, just as
the longer grammar prose remains in `grammar/`.

`scripts/import_existing_tex.py` records how the initial YAML data was
migrated from the former handwritten `verbs/verb-list.tex`. It is retained as
migration history and is not part of the normal editing workflow.

The November 2026 linguistic review and its validation scope are documented in
[docs/verb-audit-2026-11.md](docs/verb-audit-2026-11.md).
