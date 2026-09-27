"""Validation and LaTeX rendering for the structured German verb catalogue."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterator

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "verbs" / "verbs.yaml"
OUTPUT_FILE = ROOT / "verbs" / "verb-list.tex"

PERSONS = ("ich", "du", "er_sie_es", "wir", "ihr", "sie_sie")
IMPERATIVES = ("du", "wir", "ihr", "formal")
STYLES = {"default", "nom", "acc", "dat", "gen", "modal", "sep"}
VERB_TYPES = {"regular", "irregular", "mixed", "modal", "variable"}
LAYOUTS = {"inline", "stacked"}
GOVERNMENT = {
    "nominative": "Nom",
    "accusative": "Akk",
    "dative": "Dat",
    "genitive": "Gen",
    "infinitive": "Inf",
    "location": "Ort",
}


class ValidationError(ValueError):
    """Raised when the YAML catalogue does not satisfy its schema."""


def require_string(value: Any, location: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{location} must be a non-empty string")


def require_exact_keys(value: Any, expected: set[str], location: str) -> None:
    if not isinstance(value, dict):
        raise ValidationError(f"{location} must be a mapping")
    missing = expected - set(value)
    extra = set(value) - expected
    if missing or extra:
        raise ValidationError(
            f"{location} fields differ from schema; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )


def validate_forms(value: Any, location: str) -> None:
    require_exact_keys(value, set(PERSONS), location)
    for person in PERSONS:
        require_string(value[person], f"{location}.{person}")


def validate_tense(value: Any, location: str) -> None:
    require_exact_keys(value, {"auxiliaries", "reflexive", "form"}, location)
    auxiliaries = value["auxiliaries"]
    if not isinstance(auxiliaries, list) or not auxiliaries:
        raise ValidationError(f"{location}.auxiliaries must be a non-empty list")
    for auxiliary in auxiliaries:
        require_string(auxiliary, f"{location}.auxiliaries item")
    if not isinstance(value["reflexive"], bool):
        raise ValidationError(f"{location}.reflexive must be true or false")
    require_string(value["form"], f"{location}.form")


def iter_verbs(document: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for chapter in document["chapters"]:
        for group in chapter["groups"]:
            yield from group["verbs"]


def validate_document(document: Any) -> dict[str, Any]:
    require_exact_keys(document, {"schema_version", "chapters"}, "root")
    if document["schema_version"] != 1:
        raise ValidationError("root.schema_version must be 1")
    if not isinstance(document["chapters"], list) or not document["chapters"]:
        raise ValidationError("root.chapters must be a non-empty list")

    seen: set[str] = set()
    for chapter_index, chapter in enumerate(document["chapters"]):
        chapter_location = f"chapters[{chapter_index}]"
        require_exact_keys(chapter, {"title", "introduction", "groups"}, chapter_location)
        require_string(chapter["title"], f"{chapter_location}.title")
        if chapter["introduction"] is not None:
            require_string(chapter["introduction"], f"{chapter_location}.introduction")
            intro = ROOT / chapter["introduction"]
            if not intro.is_file():
                raise ValidationError(f"{chapter_location}.introduction does not exist: {intro}")
        if not isinstance(chapter["groups"], list) or not chapter["groups"]:
            raise ValidationError(f"{chapter_location}.groups must be non-empty")

        for group_index, group in enumerate(chapter["groups"]):
            group_location = f"{chapter_location}.groups[{group_index}]"
            require_exact_keys(group, {"title", "verbs"}, group_location)
            if group["title"] is not None:
                require_string(group["title"], f"{group_location}.title")
            if not isinstance(group["verbs"], list) or not group["verbs"]:
                raise ValidationError(f"{group_location}.verbs must be non-empty")

            for verb_index, verb in enumerate(group["verbs"]):
                location = f"{group_location}.verbs[{verb_index}]"
                expected = {
                    "lemma", "english", "grammar", "conjugation",
                    "compound_tenses", "prepositional_uses",
                    "separable_compounds", "bottom_layout",
                }
                require_exact_keys(verb, expected, location)
                require_string(verb["lemma"], f"{location}.lemma")
                require_string(verb["english"], f"{location}.english")
                if verb["lemma"] in seen:
                    raise ValidationError(f"duplicate verb headword: {verb['lemma']}")
                seen.add(verb["lemma"])

                grammar = verb["grammar"]
                require_exact_keys(grammar, {"type", "auxiliaries", "style"}, f"{location}.grammar")
                require_string(grammar["type"], f"{location}.grammar.type")
                if grammar["type"] not in VERB_TYPES:
                    raise ValidationError(
                        f"{location}.grammar.type is not recognized: {grammar['type']}"
                    )
                if not isinstance(grammar["auxiliaries"], list) or not grammar["auxiliaries"]:
                    raise ValidationError(f"{location}.grammar.auxiliaries must be non-empty")
                for auxiliary in grammar["auxiliaries"]:
                    if auxiliary not in {"haben", "sein"}:
                        raise ValidationError(f"{location}.grammar has unknown auxiliary {auxiliary}")
                if grammar["style"] not in STYLES:
                    raise ValidationError(f"{location}.grammar.style is not recognized")

                conjugation = verb["conjugation"]
                require_exact_keys(
                    conjugation,
                    {"present", "preterite", "subjunctive_ii", "imperative"},
                    f"{location}.conjugation",
                )
                validate_forms(conjugation["present"], f"{location}.conjugation.present")
                validate_forms(conjugation["preterite"], f"{location}.conjugation.preterite")
                if conjugation["subjunctive_ii"] is not None:
                    validate_forms(
                        conjugation["subjunctive_ii"],
                        f"{location}.conjugation.subjunctive_ii",
                    )
                imperative = conjugation["imperative"]
                if imperative is not None:
                    require_exact_keys(imperative, set(IMPERATIVES), f"{location}.conjugation.imperative")
                    for role in IMPERATIVES:
                        require_string(imperative[role], f"{location}.conjugation.imperative.{role}")

                tenses = verb["compound_tenses"]
                require_exact_keys(tenses, {"perfect", "future", "pluperfect"}, f"{location}.compound_tenses")
                for tense in ("perfect", "future", "pluperfect"):
                    validate_tense(tenses[tense], f"{location}.compound_tenses.{tense}")

                uses = verb["prepositional_uses"]
                if not isinstance(uses, list):
                    raise ValidationError(f"{location}.prepositional_uses must be a list")
                for use_index, use in enumerate(uses):
                    use_location = f"{location}.prepositional_uses[{use_index}]"
                    require_exact_keys(use, {"patterns", "meaning"}, use_location)
                    require_string(use["meaning"], f"{use_location}.meaning")
                    if not isinstance(use["patterns"], list) or not use["patterns"]:
                        raise ValidationError(f"{use_location}.patterns must be non-empty")
                    for pattern_index, pattern in enumerate(use["patterns"]):
                        pattern_location = f"{use_location}.patterns[{pattern_index}]"
                        require_exact_keys(pattern, {"phrase", "government"}, pattern_location)
                        require_string(pattern["phrase"], f"{pattern_location}.phrase")
                        if not isinstance(pattern["government"], list) or not pattern["government"]:
                            raise ValidationError(f"{pattern_location}.government must be non-empty")
                        unknown = set(pattern["government"]) - set(GOVERNMENT)
                        if unknown:
                            raise ValidationError(
                                f"{pattern_location} has unknown government {sorted(unknown)}"
                            )

                compounds = verb["separable_compounds"]
                if not isinstance(compounds, list):
                    raise ValidationError(f"{location}.separable_compounds must be a list")
                for compound_index, compound in enumerate(compounds):
                    compound_location = f"{location}.separable_compounds[{compound_index}]"
                    require_exact_keys(compound, {"lemma", "english", "split_form"}, compound_location)
                    for key in ("lemma", "english", "split_form"):
                        require_string(compound[key], f"{compound_location}.{key}")
                    if "|" not in compound["split_form"]:
                        raise ValidationError(f"{compound_location}.split_form must contain |")
                    if compound["lemma"] in seen:
                        raise ValidationError(f"duplicate verb headword: {compound['lemma']}")
                    seen.add(compound["lemma"])

                if verb["bottom_layout"] not in LAYOUTS:
                    raise ValidationError(f"{location}.bottom_layout is not recognized")

    return document


def load_document(path: Path = DATA_FILE) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValidationError(f"invalid YAML in {path}: {error}") from error
    return validate_document(document)


LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "…": r"\ldots{}",
}


def latex_plain(value: str) -> str:
    return re.sub(r"[\\&%$#_{}~^…]", lambda match: LATEX_ESCAPES[match.group()], value)


def latex_text(value: str) -> str:
    """Escape plain text and translate paired ASCII quotation marks."""
    parts = value.split('"')
    if len(parts) % 2 == 0:
        raise ValidationError(f"unpaired quotation mark in text: {value}")
    rendered: list[str] = []
    for index, part in enumerate(parts):
        escaped = latex_plain(part)
        rendered.append(f"\\enquote{{{escaped}}}" if index % 2 else escaped)
    return "".join(rendered)


def render_forms(forms: dict[str, str] | None) -> str:
    if forms is None:
        return ""
    return ",".join(latex_text(forms[person]) for person in PERSONS)


def render_imperative(imperative: dict[str, str] | None) -> str:
    if imperative is None:
        return "---"
    return ",".join(latex_text(imperative[role]) for role in IMPERATIVES)


def render_tense(tense: dict[str, Any]) -> str:
    prefix = " / ".join(latex_text(item) for item in tense["auxiliaries"])
    if tense["reflexive"]:
        prefix += " + sich"
    return f"{prefix} + \\textbf{{{latex_text(tense['form'])}}}"


def render_prepositions(uses: list[dict[str, Any]]) -> str:
    if not uses:
        return "---"
    rows = []
    for use in uses:
        rendered_patterns = []
        for pattern in use["patterns"]:
            government = " + ".join(GOVERNMENT[item] for item in pattern["government"])
            rendered_patterns.append(
                f"\\textbf{{{latex_text(pattern['phrase'])}}} + {government}"
            )
        rows.append(
            f"    & {' / '.join(rendered_patterns)} "
            f"& ({latex_text(use['meaning'])})\\\\"
        )
    return "\n" + "\n".join(rows) + "\n  "


def render_compounds(compounds: list[dict[str, Any]]) -> str:
    if not compounds:
        return "---"
    rows = []
    for compound in compounds:
        split_form = latex_text(compound["split_form"]).replace("|", "$|$")
        rows.append(
            f"    & \\relatedverb{{{latex_text(compound['lemma'])}}}"
            f"{{{latex_text(compound['english'])}}}{{{split_form}}} "
            f"& ({latex_text(compound['english'])})\\\\"
        )
    return "\n" + "\n".join(rows) + "\n  "


def render_verb(verb: dict[str, Any]) -> str:
    grammar = verb["grammar"]
    conjugation = verb["conjugation"]
    tenses = verb["compound_tenses"]
    fields = [
        f"  name = {{{latex_text(verb['lemma'])}}}",
        f"  english = {{{latex_text(verb['english'])}}}",
        f"  type = {{{latex_text(grammar['type'])}}}",
        f"  auxiliary = {{{' / '.join(grammar['auxiliaries'])}}}",
        f"  style = {{{grammar['style']}}}",
        f"  present = {{{render_forms(conjugation['present'])}}}",
        f"  preterite = {{{render_forms(conjugation['preterite'])}}}",
        f"  subjunctive = {{{render_forms(conjugation['subjunctive_ii'])}}}",
        f"  imperative = {{{render_imperative(conjugation['imperative'])}}}",
        f"  perfect = {{{render_tense(tenses['perfect'])}}}",
        f"  future = {{{render_tense(tenses['future'])}}}",
        f"  pluperfect = {{{render_tense(tenses['pluperfect'])}}}",
        f"  prepositions = {{{render_prepositions(verb['prepositional_uses'])}}}",
        f"  separable = {{{render_compounds(verb['separable_compounds'])}}}",
    ]
    if verb["bottom_layout"] != "inline":
        fields.append(f"  bottom-layout = {{{verb['bottom_layout']}}}")
    return "\\VerbTable{\n" + ",\n".join(fields) + "\n}\n"


def render_document(document: dict[str, Any]) -> str:
    lines = [
        "% Generated from verbs/verbs.yaml by scripts/generate_verbs.py.",
        "% Do not edit this file directly.",
        "",
    ]
    for chapter in document["chapters"]:
        lines.append(f"\\chapter{{{latex_text(chapter['title'])}}}")
        lines.append("")
        if chapter["introduction"]:
            introduction = Path(chapter["introduction"]).with_suffix("")
            lines.append(f"\\input{{{introduction.as_posix()}}}")
            lines.append("")
        for group in chapter["groups"]:
            if group["title"]:
                lines.append(f"\\section{{{latex_text(group['title'])}}}")
                lines.append("")
            for verb in group["verbs"]:
                lines.append(render_verb(verb))
    return "\n".join(lines).rstrip() + "\n"
