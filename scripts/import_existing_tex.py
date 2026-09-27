#!/usr/bin/env python3
"""One-time importer for the original LaTeX verb catalogue."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "verbs" / "verb-list.tex"
DEFAULT_OUTPUT = ROOT / "verbs" / "verbs.yaml"
PERSONS = ("ich", "du", "er_sie_es", "wir", "ihr", "sie_sie")
IMPERATIVES = ("du", "wir", "ihr", "formal")
GOVERNMENT = {
    "Nom": "nominative",
    "Akk": "accusative",
    "Dat": "dative",
    "Gen": "genitive",
    "Inf": "infinitive",
    "Ort": "location",
}
INTRODUCTIONS = {
    "Auxiliary Verbs": "verbs/introductions/table-convention.tex",
    "Alphabetical Verb Tables": "verbs/introductions/coverage-note.tex",
}


class ImportError(ValueError):
    pass


def extract_braced(text: str, opening: int) -> tuple[str, int]:
    if text[opening] != "{":
        raise ImportError(f"expected opening brace at offset {opening}")
    depth = 1
    index = opening + 1
    while index < len(text) and depth:
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
        index += 1
    if depth:
        raise ImportError(f"unclosed brace at offset {opening}")
    return text[opening + 1:index - 1], index


def parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    index = 0
    while True:
        while index < len(body) and (body[index].isspace() or body[index] == ","):
            index += 1
        if index >= len(body):
            return fields
        key_start = index
        while index < len(body) and (body[index].isalnum() or body[index] == "-"):
            index += 1
        key = body[key_start:index]
        while index < len(body) and (body[index].isspace() or body[index] == "="):
            index += 1
        if not key or index >= len(body) or body[index] != "{":
            raise ImportError(f"cannot parse table field near {body[key_start:key_start + 40]!r}")
        value, index = extract_braced(body, index)
        fields[key] = value


def plain_text(value: str) -> str:
    value = re.sub(r"\\enquote\{([^{}]*)\}", r'"\1"', value)
    return value.replace(r"\ldots{}", "…").replace(r"\ldots", "…")


def parse_forms(value: str) -> dict[str, str]:
    forms = value.split(",")
    if len(forms) != len(PERSONS):
        raise ImportError(f"expected six conjugated forms, received {value!r}")
    return dict(zip(PERSONS, forms))


def parse_imperative(value: str) -> dict[str, str] | None:
    if value == "---":
        return None
    forms = value.split(",")
    if len(forms) != len(IMPERATIVES):
        raise ImportError(f"expected four imperative forms, received {value!r}")
    return dict(zip(IMPERATIVES, forms))


def parse_tense(value: str) -> dict[str, Any]:
    match = re.fullmatch(r"(.*?)\s*\+\s*\\textbf\{(.*)\}", value, re.DOTALL)
    if not match:
        raise ImportError(f"cannot parse compound tense {value!r}")
    prefix, form = match.groups()
    reflexive = prefix.endswith(" + sich")
    if reflexive:
        prefix = prefix.removesuffix(" + sich")
    return {
        "auxiliaries": prefix.split(" / "),
        "reflexive": reflexive,
        "form": plain_text(form),
    }


def parse_prepositions(value: str) -> list[dict[str, Any]]:
    if value.strip() == "---":
        return []
    uses = []
    for raw_row in value.split(r"\\"):
        row = raw_row.strip().strip(",").strip()
        if not row:
            continue
        match = re.fullmatch(
            r"&\s*(.*?)\s*&\s*\((.*)\)",
            row,
            re.DOTALL,
        )
        if not match:
            raise ImportError(f"cannot parse prepositional row {row!r}")
        raw_patterns, meaning = match.groups()
        patterns = []
        for raw_pattern in raw_patterns.split(" / "):
            pattern_match = re.fullmatch(
                r"\\textbf\{(.*?)\}\s*\+\s*(.*)",
                raw_pattern.strip(),
                re.DOTALL,
            )
            if not pattern_match:
                raise ImportError(f"cannot parse governed pattern {raw_pattern!r}")
            phrase, government = pattern_match.groups()
            try:
                structured_government = [GOVERNMENT[item] for item in government.split(" + ")]
            except KeyError as error:
                raise ImportError(f"unknown government in {row!r}") from error
            patterns.append({
                "phrase": plain_text(phrase),
                "government": structured_government,
            })
        uses.append({
            "patterns": patterns,
            "meaning": plain_text(meaning),
        })
    return uses


def parse_compounds(value: str) -> list[dict[str, str]]:
    if value.strip().rstrip(",") == "---":
        return []
    compounds = []
    for raw_row in value.split(r"\\"):
        row = raw_row.strip().strip(",").strip()
        if not row:
            continue
        match = re.fullmatch(
            r"&\s*\\relatedverb\{(.*?)\}\{(.*?)\}\{(.*?)\}\s*&\s*\((.*)\)",
            row,
            re.DOTALL,
        )
        if not match:
            raise ImportError(f"cannot parse separable row {row!r}")
        lemma, english, split_form, repeated_english = match.groups()
        if english != repeated_english:
            raise ImportError(f"separable meaning mismatch in {row!r}")
        compounds.append({
            "lemma": plain_text(lemma),
            "english": plain_text(english),
            "split_form": plain_text(split_form).replace("$|$", "|"),
        })
    return compounds


def simplify_type(value: str) -> str:
    """Reduce legacy display labels to the catalogue's conjugation classes."""
    value = plain_text(value)
    lowered = value.lower()
    if lowered in {"regular", "irregular", "mixed", "modal", "variable"}:
        return lowered
    if value in {
        "strong / regular (meaning-dependent)",
        "regular / irregular variants",
    }:
        return "variable"
    if lowered.startswith("modal"):
        return "modal"
    if lowered.startswith("mixed"):
        return "mixed"
    if "irregular" in lowered or "strong" in lowered:
        return "irregular"
    if "regular" in lowered:
        return "regular"
    raise ImportError(f"unknown verb type {value!r}")


def convert_verb(fields: dict[str, str]) -> dict[str, Any]:
    required = {
        "name", "english", "type", "auxiliary", "style", "present",
        "preterite", "subjunctive", "imperative", "perfect", "future",
        "pluperfect", "prepositions", "separable",
    }
    unknown = set(fields) - required - {"bottom-layout"}
    missing = required - set(fields)
    if unknown or missing:
        raise ImportError(f"field mismatch for {fields.get('name')}: missing={missing}, unknown={unknown}")
    return {
        "lemma": plain_text(fields["name"]),
        "english": plain_text(fields["english"]),
        "grammar": {
            "type": simplify_type(fields["type"]),
            "auxiliaries": fields["auxiliary"].split(" / "),
            "style": fields["style"],
        },
        "conjugation": {
            "present": parse_forms(fields["present"]),
            "preterite": parse_forms(fields["preterite"]),
            "subjunctive_ii": parse_forms(fields["subjunctive"]) if fields["subjunctive"] else None,
            "imperative": parse_imperative(fields["imperative"]),
        },
        "compound_tenses": {
            "perfect": parse_tense(fields["perfect"]),
            "future": parse_tense(fields["future"]),
            "pluperfect": parse_tense(fields["pluperfect"]),
        },
        "prepositional_uses": parse_prepositions(fields["prepositions"]),
        "separable_compounds": parse_compounds(fields["separable"]),
        "bottom_layout": fields.get("bottom-layout", "inline"),
    }


def import_catalogue(text: str) -> dict[str, Any]:
    document: dict[str, Any] = {"schema_version": 1, "chapters": []}
    current_chapter: dict[str, Any] | None = None
    current_group: dict[str, Any] | None = None
    cursor = 0
    event_pattern = re.compile(
        r"^\\chapter\{([^{}]+)\}|^\\section\{([^{}]+)\}|^\\VerbTable\{",
        re.MULTILINE,
    )
    while match := event_pattern.search(text, cursor):
        chapter_title, section_title = match.group(1), match.group(2)
        if chapter_title is not None:
            current_chapter = {
                "title": chapter_title,
                "introduction": INTRODUCTIONS.get(chapter_title),
                "groups": [],
            }
            document["chapters"].append(current_chapter)
            current_group = None
            cursor = match.end()
        elif section_title is not None:
            if current_chapter is None:
                raise ImportError("section encountered before chapter")
            current_group = {"title": section_title, "verbs": []}
            current_chapter["groups"].append(current_group)
            cursor = match.end()
        else:
            if current_chapter is None:
                raise ImportError("verb table encountered before chapter")
            if current_group is None:
                current_group = {"title": None, "verbs": []}
                current_chapter["groups"].append(current_group)
            body, cursor = extract_braced(text, match.end() - 1)
            current_group["verbs"].append(convert_verb(parse_fields(body)))
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        document = import_catalogue(args.source.read_text(encoding="utf-8"))
    except (OSError, ImportError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    count = sum(
        len(group["verbs"])
        for chapter in document["chapters"]
        for group in chapter["groups"]
    )
    print(f"imported {count} verbs from {args.source} into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
