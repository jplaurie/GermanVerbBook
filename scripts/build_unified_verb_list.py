#!/usr/bin/env python3
"""Reproduce the initial unified LaTeX list from the legacy source files.

Run from the repository root:
    python3 scripts/build_unified_verb_list.py /tmp/verb-list.tex

The generated file was committed as verbs/verb-list.tex. This importer is
retained only to make the one-time migration auditable; verb-list.tex is now
the canonical source and should be edited directly.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD_LETTERS = tuple("abcdefghiklmnopqrstuvwz")
HEADINGS = (
    "PRÄSENS",
    "PRÄTERITUM",
    "KONJUNKTIV II",
    "IMPERATIV",
    "PERFEKT",
    "FUTURE I",
    "PLUSQUAMPERFEKT",
    "MIT PRÄPOSITIONEN",
    "TRENNBARE VERBEN",
)


@dataclass
class Verb:
    category: str
    name: str
    english: str
    verb_type: str
    auxiliary: str
    style: str
    present: str
    preterite: str
    subjunctive: str
    imperative: str
    perfect: str
    future: str
    pluperfect: str
    prepositions: str
    separable: str
    source: str
    bottom_layout: str = "inline"


def uncommented(text: str) -> str:
    """Remove LaTeX comments while retaining real source lines."""
    clean = []
    for line in text.splitlines():
        match = re.search(r"(?<!\\)%", line)
        clean.append(line[: match.start()] if match else line)
    return "\n".join(clean)


def braced_arguments(text: str, start: int, count: int) -> tuple[list[str], int]:
    """Read count balanced braced arguments starting at or after start."""
    args: list[str] = []
    pos = start
    for _ in range(count):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text) or text[pos] != "{":
            raise ValueError(f"expected argument {len(args) + 1} near {text[pos:pos+60]!r}")
        depth = 0
        begin = pos + 1
        while pos < len(text):
            if text[pos] == "{" and (pos == 0 or text[pos - 1] != "\\"):
                depth += 1
            elif text[pos] == "}" and (pos == 0 or text[pos - 1] != "\\"):
                depth -= 1
                if depth == 0:
                    args.append(text[begin:pos].strip())
                    pos += 1
                    break
            pos += 1
        else:
            raise ValueError("unterminated braced argument")
    return args, pos


def metadata(options: str, key: str) -> str:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*", options)
    if not match:
        raise ValueError(f"missing {key} in {options!r}")
    values, _ = braced_arguments(options, match.end(), 1)
    return values[0]


def tables(block: str) -> dict[str, str]:
    found: dict[str, str] = {}
    pattern = re.compile(
        r"\\begin\{tabular\}(?:\[[^\]]*\])?\{[^\n]*\}(.*?)\\end\{tabular\}",
        re.S,
    )
    for match in pattern.finditer(uncommented(block)):
        body = match.group(1)
        heading = next(
            (item for item in HEADINGS if re.search(rf"\\textbf\{{{re.escape(item)}\}}\s*", body)),
            None,
        )
        if heading is not None and heading not in found:
            found[heading] = body
    return found


def bold_values(body: str, heading: str) -> list[str]:
    values = re.findall(r"\\textbf\{([^{}]*)\}", body)
    return [value.strip() for value in values if value.strip() != heading]


def six_forms(table_map: dict[str, str], heading: str, source: str) -> str:
    values = bold_values(table_map[heading], heading)
    if len(values) != 6:
        raise ValueError(f"{source}: {heading} has {len(values)} forms: {values}")
    return ",".join(values)


def imperative_forms(table_map: dict[str, str], source: str) -> str:
    values = bold_values(table_map["IMPERATIV"], "IMPERATIV")
    if values and all(value in {"-", "--", "---"} for value in values):
        return "---"
    if len(values) != 4:
        raise ValueError(f"{source}: IMPERATIV has {len(values)} forms: {values}")
    return ",".join(values)


def formula(table_map: dict[str, str], heading: str, source: str) -> str:
    body = table_map[heading]
    lines = [line.strip() for line in body.splitlines()]
    for line in lines[1:]:
        if "&" not in line or "multicolumn" in line:
            continue
        value = line.split("&", 1)[1].strip()
        value = re.sub(r"\\\\\s*$", "", value).strip()
        if value:
            return value
    raise ValueError(f"{source}: could not read {heading}")


def bottom_rows(table_map: dict[str, str], heading: str) -> str:
    body = table_map[heading]
    lines = [line.strip() for line in body.splitlines()]
    rows = [
        line
        for line in lines[1:]
        if line and "&" in line and "multicolumn" not in line and "\\vspace" not in line
    ]
    non_heading_bold = bold_values(body, heading)
    if not rows or (
        non_heading_bold
        and all(value in {"-", "--", "---"} for value in non_heading_bold)
    ):
        return "---"
    return "\n".join(rows)


def parse_old_file(path: Path, category: str) -> list[Verb]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\\begin\{verbentry\}\{(.*?)\n\}(.*?)\\end\{verbentry\}",
        re.S,
    )
    result: list[Verb] = []
    for number, match in enumerate(pattern.finditer(text), 1):
        options, body = match.groups()
        source = f"{path.relative_to(ROOT)}:{number}"
        table_map = tables(body)
        missing = set(HEADINGS) - set(table_map)
        missing.discard("KONJUNKTIV II")
        if missing:
            raise ValueError(f"{source}: missing tables {sorted(missing)}")
        result.append(
            Verb(
                category=category,
                name=metadata(options, "name"),
                english=metadata(options, "english"),
                verb_type=metadata(options, "type"),
                auxiliary=metadata(options, "auxiliary"),
                style=metadata(options, "style"),
                present=six_forms(table_map, "PRÄSENS", source),
                preterite=six_forms(table_map, "PRÄTERITUM", source),
                subjunctive=(
                    six_forms(table_map, "KONJUNKTIV II", source)
                    if "KONJUNKTIV II" in table_map
                    else ""
                ),
                imperative=imperative_forms(table_map, source),
                perfect=formula(table_map, "PERFEKT", source),
                future=formula(table_map, "FUTURE I", source),
                pluperfect=formula(table_map, "PLUSQUAMPERFEKT", source),
                prepositions=bottom_rows(table_map, "MIT PRÄPOSITIONEN"),
                separable=bottom_rows(table_map, "TRENNBARE VERBEN"),
                source=source,
            )
        )
    return result


def past_auxiliary(auxiliary: str) -> str:
    if auxiliary == "sein":
        return "waren"
    if auxiliary == "haben / sein":
        return "hatten / waren"
    return "hatten"


def is_separable_entry(verb: Verb) -> bool:
    """Return true for standalone separable compounds, not 'inseparable'."""
    type_words = re.split(r"[\s,/]+", verb.verb_type.casefold())
    return "separable" in type_words or verb.name == "sich anstrengen"


def stem_entry(
    name: str,
    english: str,
    verb_type: str,
    present: str,
    preterite: str,
    imperative: str,
    participle: str,
) -> Verb:
    """Create a missing base verb needed to host separable compounds."""
    return Verb(
        category=name[0].upper(),
        name=name,
        english=english,
        verb_type=verb_type,
        auxiliary="haben",
        style="default",
        present=present,
        preterite=preterite,
        subjunctive="",
        imperative=imperative,
        perfect=rf"haben + \textbf{{{participle}}}",
        future=rf"werden + \textbf{{{name}}}",
        pluperfect=rf"hatten + \textbf{{{participle}}}",
        prepositions="---",
        separable="---",
        source="new stem entry",
    )


MISSING_STEMS = (
    stem_entry(
        "biegen",
        "to bend",
        "strong / irregular",
        "biege,biegst,biegt,biegen,biegt,biegen",
        "bog,bogst,bog,bogen,bogt,bogen",
        "bieg(e) (du)!,biegen wir!,biegt (ihr)!,biegen Sie!",
        "gebogen",
    ),
    stem_entry(
        "melden",
        "to report / notify",
        "regular",
        "melde,meldest,meldet,melden,meldet,melden",
        "meldete,meldetest,meldete,meldeten,meldetet,meldeten",
        "melde (du)!,melden wir!,meldet (ihr)!,melden Sie!",
        "gemeldet",
    ),
    stem_entry(
        "regen",
        "to stir / move",
        "regular",
        "rege,regst,regt,regen,regt,regen",
        "regte,regtest,regte,regten,regtet,regten",
        "reg(e) (du)!,regen wir!,regt (ihr)!,regen Sie!",
        "geregt",
    ),
    stem_entry(
        "richten",
        "to direct / arrange",
        "regular",
        "richte,richtest,richtet,richten,richtet,richten",
        "richtete,richtetest,richtete,richteten,richtetet,richteten",
        "richte (du)!,richten wir!,richtet (ihr)!,richten Sie!",
        "gerichtet",
    ),
    stem_entry(
        "räumen",
        "to clear / vacate",
        "regular",
        "räume,räumst,räumt,räumen,räumt,räumen",
        "räumte,räumtest,räumte,räumten,räumtet,räumten",
        "räum(e) (du)!,räumen wir!,räumt (ihr)!,räumen Sie!",
        "geräumt",
    ),
    stem_entry(
        "schnallen",
        "to fasten / buckle",
        "regular",
        "schnalle,schnallst,schnallt,schnallen,schnallt,schnallen",
        "schnallte,schnalltest,schnallte,schnallten,schnalltet,schnallten",
        "schnall(e) (du)!,schnallen wir!,schnallt (ihr)!,schnallen Sie!",
        "geschnallt",
    ),
    stem_entry(
        "strengen",
        "to strain",
        "regular",
        "strenge,strengst,strengt,strengen,strengt,strengen",
        "strengte,strengtest,strengte,strengten,strengtet,strengten",
        "streng(e) (du)!,strengen wir!,strengt (ihr)!,strengen Sie!",
        "gestrengt",
    ),
    stem_entry(
        "wachen",
        "to be awake / keep watch",
        "regular",
        "wache,wachst,wacht,wachen,wacht,wachen",
        "wachte,wachtest,wachte,wachten,wachtet,wachten",
        "wach(e) (du)!,wachen wir!,wacht (ihr)!,wachen Sie!",
        "gewacht",
    ),
    stem_entry(
        "weisen",
        "to point / show",
        "strong / irregular",
        "weise,weist,weist,weisen,weist,weisen",
        "wies,wiesest,wies,wiesen,wiest,wiesen",
        "weise (du)!,weisen wir!,weist (ihr)!,weisen Sie!",
        "gewiesen",
    ),
)


SEPARABLE_TARGET_OVERRIDES = {
    "herstellen": "stellen",
    "herunterfahren": "fahren",
}

INSEPARABLE_PREFIXES = {"be", "emp", "ent", "er", "ge", "miss", "ver", "zer"}


def parse_related_rows(value: str, source: str) -> dict[str, list[str | None]]:
    """Parse existing related-verb rows into a normalized display map."""
    if value == "---":
        return {}
    rows: dict[str, list[str | None]] = {}
    pattern = re.compile(
        r"^\s*&\s*(?:\\textbf\{(?P<bold>.+?)\}|(?P<plain>[^&]+?))"
        r"\s*&\s*\((?P<english>.*)\)\s*(?:\\\\)?\s*$"
    )
    for line in value.splitlines():
        if re.match(r"^\s*&\s*--+\s*&\s*--+", line):
            continue
        match = pattern.match(line)
        if not match:
            raise ValueError(f"{source}: cannot parse related-verb row {line!r}")
        display = (match.group("bold") or match.group("plain")).strip()
        english = match.group("english").strip()
        normalized = display.replace("$", "").replace(" ", "")
        prefix = normalized.removeprefix("sich").split("|", 1)[0]
        if prefix in INSEPARABLE_PREFIXES:
            continue
        rows.setdefault(normalized, [display, english, None])
    return rows


def render_related_rows(rows: dict[str, list[str | None]]) -> str:
    rendered = []
    for normalized in sorted(rows):
        display, english, index_name = rows[normalized]
        if index_name is None:
            cell = rf"\textbf{{{display}}}"
        else:
            cell = rf"\relatedverb{{{index_name}}}{{{english}}}{{{display}}}"
        rendered.append(rf"& {cell} & ({english})\\")
    return "\n".join(rendered) if rendered else "---"


def consolidate_separable_verbs(groups: dict[str, list[Verb]]) -> int:
    """Move standalone separable compounds beneath their base verb."""
    imported = [verb for group in groups.values() for verb in group]
    if len(imported) != 715:
        raise ValueError(f"expected 715 imported verbs, found {len(imported)}")

    existing_names = {verb.name for verb in imported}
    for stem in MISSING_STEMS:
        if stem.name not in existing_names:
            groups[stem.category].append(stem)
            existing_names.add(stem.name)

    all_verbs = [verb for group in groups.values() for verb in group]
    by_name = {verb.name: verb for verb in all_verbs}
    related_rows = {
        verb.name: parse_related_rows(verb.separable, verb.source)
        for verb in all_verbs
    }
    separable = [verb for verb in all_verbs if is_separable_entry(verb)]
    additions: dict[str, list[Verb]] = {}

    for compound in separable:
        bare_name = re.sub(r"^sich\s+", "", compound.name)
        target_name = SEPARABLE_TARGET_OVERRIDES.get(compound.name)
        if target_name is None:
            candidates = [
                name
                for name in by_name
                if not name.startswith("sich ")
                and name != bare_name
                and bare_name.endswith(name)
            ]
            if not candidates:
                raise ValueError(f"{compound.name}: no base verb found")
            target_name = max(candidates, key=len)
        additions.setdefault(target_name, []).append(compound)

    for target_name, compounds in additions.items():
        rows = related_rows[target_name]
        for compound in compounds:
            bare_name = re.sub(r"^sich\s+", "", compound.name)
            prefix = bare_name[: -len(target_name)]
            display = prefix + "$|$" + target_name
            if compound.name.startswith("sich "):
                display = "sich " + display
            normalized = display.replace("$", "").replace(" ", "")
            rows[normalized] = [display, compound.english, compound.name]
    for verb in all_verbs:
        verb.separable = render_related_rows(related_rows[verb.name])

    separable_ids = {id(verb) for verb in separable}
    for category in groups:
        groups[category] = [
            verb for verb in groups[category] if id(verb) not in separable_ids
        ]
    return len(separable)


def parse_b1_file(path: Path, category: str) -> list[Verb]:
    text = uncommented(path.read_text(encoding="utf-8"))
    result: list[Verb] = []
    pos = 0
    number = 0
    marker = r"\BOneVerb"
    while True:
        pos = text.find(marker, pos)
        if pos < 0:
            break
        number += 1
        args, pos = braced_arguments(text, pos + len(marker), 9)
        display_name, infinitive, english, verb_type, auxiliary, present, past, imperative, participle = args
        source = f"{path.relative_to(ROOT)}:{number}"
        if len(present.split(",")) != 6 or len(past.split(",")) != 6:
            raise ValueError(f"{source}: expected six present and preterite forms")
        if imperative != "---" and len(imperative.split(",")) != 4:
            raise ValueError(f"{source}: expected four imperative forms or ---")
        result.append(
            Verb(
                category=category,
                name=display_name,
                english=english,
                verb_type=verb_type,
                auxiliary=auxiliary,
                style="default",
                present=present,
                preterite=past,
                subjunctive="",
                imperative=imperative,
                perfect=rf"{auxiliary} + \textbf{{{participle}}}",
                future=rf"werden + \textbf{{{infinitive}}}",
                pluperfect=rf"{past_auxiliary(auxiliary)} + \textbf{{{participle}}}",
                prepositions="---",
                separable="---",
                source=source,
            )
        )
    return result


def sort_key(verb: Verb) -> str:
    value = re.sub(r"^sich\s+", "", verb.name.casefold())
    value = value.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if char.isalnum() or char.isspace()
    )


def key_value(key: str, value: str, final: bool = False) -> str:
    comma = "" if final else ","
    if "\n" not in value:
        return f"  {key} = {{{value}}}{comma}\n"
    indented = "\n".join(f"    {line}" for line in value.splitlines())
    return f"  {key} = {{\n{indented}\n  }}{comma}\n"


def render_verb(verb: Verb) -> str:
    values = (
        ("name", verb.name),
        ("english", verb.english),
        ("type", verb.verb_type),
        ("auxiliary", verb.auxiliary),
        ("style", verb.style),
        ("present", verb.present),
        ("preterite", verb.preterite),
        ("subjunctive", verb.subjunctive),
        ("imperative", verb.imperative),
        ("perfect", verb.perfect),
        ("future", verb.future),
        ("pluperfect", verb.pluperfect),
        ("prepositions", verb.prepositions),
        ("separable", verb.separable),
    )
    if verb.name in {"sammeln", "trainieren"}:
        values += (("bottom-layout", "stacked"),)
    lines = [rf"% Migrated from {verb.source}", "\n", "\\VerbTable{\n"]
    for index, (key, value) in enumerate(values):
        lines.append(key_value(key, value, final=index == len(values) - 1))
    lines.append("}\n\n")
    return "".join(lines)


def build() -> str:
    groups: dict[str, list[Verb]] = {
        "Auxiliary": parse_old_file(ROOT / "verbs/auxiliary.tex", "Auxiliary"),
        "Modal": parse_old_file(ROOT / "verbs/modal.tex", "Modal"),
        "Reflexive": parse_old_file(ROOT / "verbs/reflexive.tex", "Reflexive"),
    }
    for letter in OLD_LETTERS:
        category = letter.upper()
        groups[category] = parse_old_file(ROOT / f"verbs/{letter}.tex", category)
        b1_path = ROOT / f"verbs/b1/{letter}.tex"
        if b1_path.exists():
            groups[category].extend(parse_b1_file(b1_path, category))

    # Reflexive B1 additions originally lived in the per-letter files. Keep
    # every ``sich ...`` headword together in the dedicated reflexive chapter.
    for letter in OLD_LETTERS:
        category = letter.upper()
        reflexive = [verb for verb in groups[category] if verb.name.startswith("sich ")]
        groups["Reflexive"].extend(reflexive)
        groups[category] = [verb for verb in groups[category] if not verb.name.startswith("sich ")]

    separable_count = consolidate_separable_verbs(groups)
    all_verbs = [verb for group in groups.values() for verb in group]
    table_count = len(all_verbs)
    indexed_headwords = table_count + separable_count

    output = [
        "% SINGLE CANONICAL VERB SOURCE (consolidated 2026-09-25).\n",
        "% Edit verb data here; style/germanbook.sty owns the shared layout.\n",
        "% scripts/build_unified_verb_list.py is retained only as a migration audit.\n\n",
        "\\chapter{Auxiliary Verbs}\n\n",
    ]
    output.extend(render_verb(verb) for verb in groups["Auxiliary"])
    output.append("\\chapter{Modal Verbs}\n\n")
    output.extend(render_verb(verb) for verb in groups["Modal"])
    output.append("\\chapter{Reflexive Verbs}\n\n")
    output.extend(render_verb(verb) for verb in sorted(groups["Reflexive"], key=sort_key))
    output.extend(
        [
            "\\chapter{Alphabetical Verb Tables}\n\n",
            "\\begin{tcolorbox}[colback=referenceBlueBg,colframe=genderMasculine,title={B1 coverage note}]\n",
            f"This reference contains {table_count} complete stem tables. A further {separable_count} separable compounds are listed compactly under their stems, giving {indexed_headwords} indexed verb headwords. The selection targets the verbs most useful through CEFR B1; CEFR does not prescribe one official exhaustive verb list. Each full table includes all six present and simple-past forms, four imperative forms where they exist, and the perfect, future and pluperfect constructions.\n",
            "\\end{tcolorbox}\n\n",
        ]
    )
    for letter in OLD_LETTERS:
        category = letter.upper()
        output.append(f"\\section{{{category}}}\n\n")
        output.extend(render_verb(verb) for verb in sorted(groups[category], key=sort_key))
    return "".join(output)


def main() -> None:
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "verbs/verb-list.tex"
    destination.write_text(build(), encoding="utf-8")
    print(f"wrote {destination}")


if __name__ == "__main__":
    main()
