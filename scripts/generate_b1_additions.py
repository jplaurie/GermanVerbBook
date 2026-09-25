#!/usr/bin/env python3
"""Generate compact LaTeX entries for verbs missing from the B1 reference.

The script intentionally writes only to an output directory supplied on the
command line.  It combines the official Goethe headwords with explicit
UniMorph forms; the generated TeX therefore contains data, not conjugation
rules or guesses made at typesetting time.
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


TAGS = (
    "V;IND;SG;1;PRS", "V;IND;SG;2;PRS", "V;IND;SG;3;PRS",
    "V;IND;PL;1;PRS", "V;IND;PL;2;PRS", "V;IND;PL;3;PRS",
    "V;IND;SG;1;PST", "V;IND;SG;2;PST", "V;IND;SG;3;PST",
    "V;IND;PL;1;PST", "V;IND;PL;2;PST", "V;IND;PL;3;PST",
)


TRANSLATION_OVERRIDES = {
    "abfahren": "depart / leave",
    "abgeben": "hand in / give away",
    "abheben": "withdraw / take off",
    "abhängen": "depend / hang",
    "abmachen": "arrange / agree",
    "abnehmen": "take off / lose weight / decrease",
    "abschreiben": "copy",
    "abwaschen": "wash up",
    "anmelden": "register / sign up",
    "anschaffen": "purchase / acquire",
    "anschließen": "connect / join",
    "ansehen": "look at / watch",
    "ansprechen": "address / speak to",
    "anstellen": "employ / switch on",
    "anstrengen": "exert oneself",
    "anzeigen": "display / report",
    "anziehen": "put on / get dressed",
    "auffallen": "stand out / be noticed",
    "aufführen": "perform / list",
    "aufgeben": "give up / post",
    "aufheben": "pick up / keep / cancel",
    "aufnehmen": "record / admit",
    "aufpassen": "pay attention / watch out",
    "aufregen": "upset / get worked up",
    "auftreten": "appear / occur",
    "ausfallen": "be cancelled / fail",
    "ausgeben": "spend / hand out",
    "ausgehen": "go out / assume",
    "ausmachen": "switch off / constitute",
    "ausrichten": "pass on / align",
    "ausruhen": "rest",
    "ausstellen": "issue / exhibit",
    "ausziehen": "take off / move out",
    "backen": "bake",
    "basteln": "make handicrafts",
    "bedienen": "serve / operate",
    "begegnen": "meet / encounter",
    "begleiten": "accompany",
    "berichten": "report",
    "besichtigen": "inspect / tour",
    "besorgen": "obtain / take care of",
    "beteiligen": "participate",
    "blitzen": "flash",
    "braten": "fry / roast",
    "bremsen": "brake",
    "brennen": "burn",
    "duschen": "shower",
    "einbrechen": "break in",
    "einfallen": "occur to",
    "einigen": "agree",
    "einkaufen": "shop",
    "einnehmen": "take / collect",
    "einpacken": "pack / wrap",
    "einrichten": "furnish / set up",
    "einsetzen": "insert / deploy",
    "einstellen": "hire / set / discontinue",
    "empfangen": "receive",
    "enthalten": "contain",
    "entschließen": "decide",
    "ereignen": "happen / occur",
    "erkälten": "catch a cold",
    "fassen": "grasp / hold",
    "fernsehen": "watch television",
    "festlegen": "set / determine",
    "festsetzen": "set / fix",
    "feststehen": "be certain / be fixed",
    "fotografieren": "photograph",
    "frieren": "freeze / be cold",
    "frühstücken": "have breakfast",
    "gefallen lassen": "put up with",
    "gelingen": "succeed",
    "geschehen": "happen",
    "gratulieren": "congratulate",
    "grillieren": "grill",
    "grüßen": "greet",
    "hageln": "hail",
    "handeln": "act / deal",
    "heizen": "heat",
    "herstellen": "produce / manufacture",
    "hinterlassen": "leave behind",
    "hinweisen": "point out",
    "hupen": "honk",
    "hängen": "hang",
    "klappen": "work / succeed",
    "kleben": "stick / glue",
    "klingeln": "ring",
    "klingen": "sound",
    "kämpfen": "fight",
    "küssen": "kiss",
    "langweilen": "be bored / bore",
    "leiden": "suffer",
    "leidtun": "be sorry / hurt",
    "leisten": "perform / afford",
    "leiten": "lead / manage",
    "liegen": "lie / be located",
    "lohnen": "be worthwhile",
    "lügen": "lie",
    "malen": "paint",
    "markieren": "mark / highlight",
    "messen": "measure",
    "mitteilen": "inform / tell",
    "nachdenken": "think / reflect",
    "nähern": "approach",
    "pflanzen": "plant",
    "pflegen": "care for / maintain",
    "rechnen": "calculate / expect",
    "rauchen": "smoke",
    "reiten": "ride",
    "rennen": "run",
    "runterwerfen": "throw down",
    "schimpfen": "scold / complain",
    "schießen": "shoot",
    "schreien": "shout / scream",
    "schweigen": "be silent",
    "schwimmen": "swim",
    "sichern": "secure / safeguard",
    "siegen": "win / be victorious",
    "sinken": "sink",
    "singen": "sing",
    "spazierengehen": "go for a walk",
    "spülen": "rinse / wash up",
    "spüren": "sense / feel",
    "stammen": "come from",
    "stecken": "stick / be located",
    "stinken": "stink",
    "streiken": "strike",
    "streiten": "argue",
    "stürzen": "fall / crash",
    "tanken": "refuel",
    "tanzen": "dance",
    "tauchen": "dive",
    "teilnehmen": "take part",
    "telefonieren": "make a telephone call",
    "testen": "test",
    "tippen": "type / tap",
    "treiben": "drive / do",
    "trocknen": "dry",
    "umdrehen": "turn around",
    "umgehen": "deal with / go around",
    "umsteigen": "change trains / transfer",
    "umziehen": "move house / change clothes",
    "unterrichten": "teach",
    "verabschieden": "say goodbye",
    "verbrauchen": "consume / use up",
    "vergnügen": "enjoy oneself",
    "verhalten": "behave",
    "verlaufen": "get lost / run",
    "vermieten": "rent out",
    "verpacken": "pack / package",
    "verpflegen": "provide food / care for",
    "verraten": "betray / reveal",
    "verreisen": "go away / travel",
    "verschieben": "postpone / move",
    "versäumen": "miss / fail to do",
    "vertreten": "represent / stand in for",
    "veröffentlichen": "publish",
    "vorhaben": "intend / plan",
    "vorkommen": "occur / seem",
    "vorlesen": "read aloud",
    "wandern": "hike",
    "wetten": "bet",
    "wiegen": "weigh",
    "winken": "wave",
    "zugehen": "approach / close",
    "zuhören": "listen to",
    "zusagen": "accept / promise",
    "zuschauen": "watch",
    "zelten": "camp",
    "überfahren": "run over",
    "übernachten": "stay overnight",
    "überqueren": "cross",
    "überzeugen": "convince",
}


MANUAL_FORMS = {
    "abmachen": ("mache ab,machst ab,macht ab,machen ab,macht ab,machen ab", "machte ab,machtest ab,machte ab,machten ab,machtet ab,machten ab", "mach ab,macht ab", "abgemacht"),
    "abnehmen": ("nehme ab,nimmst ab,nimmt ab,nehmen ab,nehmt ab,nehmen ab", "nahm ab,nahmst ab,nahm ab,nahmen ab,nahmt ab,nahmen ab", "nimm ab,nehmt ab", "abgenommen"),
    "ankommen": ("komme an,kommst an,kommt an,kommen an,kommt an,kommen an", "kam an,kamst an,kam an,kamen an,kamt an,kamen an", "komm an,kommt an", "angekommen"),
    "annehmen": ("nehme an,nimmst an,nimmt an,nehmen an,nehmt an,nehmen an", "nahm an,nahmst an,nahm an,nahmen an,nahmt an,nahmen an", "nimm an,nehmt an", "angenommen"),
    "ansprechen": ("spreche an,sprichst an,spricht an,sprechen an,sprecht an,sprechen an", "sprach an,sprachst an,sprach an,sprachen an,spracht an,sprachen an", "sprich an,sprecht an", "angesprochen"),
    "aufführen": ("führe auf,führst auf,führt auf,führen auf,führt auf,führen auf", "führte auf,führtest auf,führte auf,führten auf,führtet auf,führten auf", "führ auf,führt auf", "aufgeführt"),
    "einführen": ("führe ein,führst ein,führt ein,führen ein,führt ein,führen ein", "führte ein,führtest ein,führte ein,führten ein,führtet ein,führten ein", "führ ein,führt ein", "eingeführt"),
    "grüßen": ("grüße,grüßt,grüßt,grüßen,grüßt,grüßen", "grüßte,grüßtest,grüßte,grüßten,grüßtet,grüßten", "grüß,grüßt", "gegrüßt"),
    "hageln": ("hagle,hagelst,hagelt,hageln,hagelt,hageln", "hagelte,hageltest,hagelte,hagelten,hageltet,hagelten", "---,---", "gehagelt"),
    "leidtun": ("tue leid,tust leid,tut leid,tun leid,tut leid,tun leid", "tat leid,tatst leid,tat leid,taten leid,tatet leid,taten leid", "tu leid,tut leid", "leidgetan"),
    "runterwerfen": ("werfe runter,wirfst runter,wirft runter,werfen runter,werft runter,werfen runter", "warf runter,warfst runter,warf runter,warfen runter,warft runter,warfen runter", "wirf runter,werft runter", "runtergeworfen"),
    "spazierengehen": ("gehe spazieren,gehst spazieren,geht spazieren,gehen spazieren,geht spazieren,gehen spazieren", "ging spazieren,gingst spazieren,ging spazieren,gingen spazieren,gingt spazieren,gingen spazieren", "geh spazieren,geht spazieren", "spazieren gegangen"),
    "umgehen": ("gehe um,gehst um,geht um,gehen um,geht um,gehen um", "ging um,gingst um,ging um,gingen um,gingt um,gingen um", "geh um,geht um", "umgegangen"),
    "wehtun": ("tue weh,tust weh,tut weh,tun weh,tut weh,tun weh", "tat weh,tatst weh,tat weh,taten weh,tatet weh,taten weh", "tu weh,tut weh", "wehgetan"),
    "zurechtkommen": ("komme zurecht,kommst zurecht,kommt zurecht,kommen zurecht,kommt zurecht,kommen zurecht", "kam zurecht,kamst zurecht,kam zurecht,kamen zurecht,kamt zurecht,kamen zurecht", "komm zurecht,kommt zurecht", "zurechtgekommen"),
    "zählen": ("zähle,zählst,zählt,zählen,zählt,zählen", "zählte,zähltest,zählte,zählten,zähltet,zählten", "zähl,zählt", "gezählt"),
}


def normalize(value: str) -> str:
    value = value.strip().lower()
    value = {
        "(herunter-)fahren": "herunterfahren",
        "(hinunter) runterwerfen": "runterwerfen",
        "über- übertreiben": "übertreiben",
        "heraus-": "",
        "herunter-": "",
    }.get(value, value)
    value = re.sub(r"^\((?:sich|sich etwas)\)\s*", "", value)
    value = re.sub(r"^sich(?: etwas)?\s+", "", value)
    value = re.sub(r"^es\s+", "", value)
    return {
        "bekannt geben": "bekanntgeben",
        "spazieren gehen": "spazierengehen",
        "leid tun": "leidtun",
        "zu sein": "zusein",
    }.get(value, value)


def finite_imperative(form: str, pronoun: str) -> str:
    if form == "---":
        return "---"
    first, *rest = form.split(" ")
    tail = (" " + " ".join(rest)) if rest else ""
    return f"{first} ({pronoun}){tail}!"


def insert_subject(form: str, subject: str, reflexive: str = "") -> str:
    first, *rest = form.split(" ")
    middle = f" {subject}"
    if reflexive:
        middle += f" {reflexive}"
    tail = (" " + " ".join(rest)) if rest else ""
    return f"{first}{middle}{tail}!"


def insert_reflexive(form: str, pronoun: str) -> str:
    """Place the pronoun after the finite verb and before a separable prefix."""
    first, *rest = form.split()
    tail = (" " + " ".join(rest)) if rest else ""
    return f"{first} {pronoun}{tail}"


def verb_type(past: str, participle: str, separable: bool) -> str:
    mixed = {"brennen", "rennen", "senden", "wenden"}
    if past.split()[0].endswith(("te", "ete")):
        kind = "mixed" if CURRENT_LEMMA in mixed else "regular"
    else:
        kind = "strong / irregular"
    return f"separable, {kind}" if separable else kind


parser = argparse.ArgumentParser()
parser.add_argument("--missing", type=Path, required=True)
parser.add_argument("--translations", type=Path, required=True)
parser.add_argument("--unimorph", type=Path, required=True)
parser.add_argument("--bbox", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()

missing = set(args.missing.read_text(encoding="utf-8").splitlines())
translations = {}
for line in args.translations.read_text(encoding="utf-8").splitlines():
    lemma, gloss = line.split("\t", 1)
    translations[lemma] = TRANSLATION_OVERRIDES.get(lemma, gloss.strip().rstrip(" .?!"))

forms: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
with args.unimorph.open(encoding="utf-8") as source:
    for line in source:
        lemma, form, tag = line.rstrip("\n").split("\t")
        if lemma in missing and form not in forms[lemma][tag]:
            forms[lemma][tag].append(form)

# Recover Goethe's reflexive marking and perfect auxiliary from its headword
# blocks.  The extra manually supplied items repair rare PDF column collisions.
ns = {"x": "http://www.w3.org/1999/xhtml"}
root = ET.parse(args.bbox).getroot()
official: dict[str, tuple[str, str]] = {}
for block in root.findall(".//x:block", ns):
    x = float(block.attrib["xMin"])
    cutoff = 128 if x < 130 else 410
    words = [
        (w.text or "") for w in block.findall(".//x:word", ns)
        if float(w.attrib["xMin"]) < cutoff
    ]
    text = " ".join(words)
    if not ((25 < x < 125 or 300 < x < 410) and text.count(",") >= 3):
        continue
    headword = text.split(",", 1)[0].strip()
    if re.match(r"^(der|die|das|\d)", headword, re.I):
        continue
    lemma = normalize(headword)
    if lemma:
        official[lemma] = (headword, text)
for lemma in ("schlafen", "besitzen", "transportieren", "herausfinden", "herunterladen", "herunterfahren", "runterwerfen"):
    official.setdefault(lemma, (lemma, ""))

args.out.mkdir(parents=True, exist_ok=True)
by_letter: dict[str, list[str]] = defaultdict(list)
global CURRENT_LEMMA

for lemma in sorted(missing, key=lambda s: s.translate(str.maketrans("äöüß", "aous"))):
    CURRENT_LEMMA = lemma
    headword, source_text = official.get(lemma, (lemma, ""))
    mandatory_reflexive = headword.startswith("sich ") and lemma != "umziehen"
    display = f"sich {lemma}" if mandatory_reflexive else lemma
    infinitive = display

    if lemma in MANUAL_FORMS:
        present_csv, past_csv, imp_csv, participle = MANUAL_FORMS[lemma]
        present = present_csv.split(",")
        past = past_csv.split(",")
        imp_sg, imp_pl = imp_csv.split(",")
    else:
        dataset = forms[lemma]
        if any(not dataset[tag] for tag in TAGS) or not dataset["V.PTCP;PST"]:
            raise SystemExit(f"Incomplete paradigm for {lemma}")
        present = [dataset[tag][0].strip() for tag in TAGS[:6]]
        past = [dataset[tag][0].strip() for tag in TAGS[6:]]
        imp_sg = min(dataset["V;IMP;SG;2"], key=len).strip()
        imp_pl = dataset["V;IMP;PL;2"][0].strip()
        participle = dataset["V.PTCP;PST"][0].strip()

    # The official headword column is authoritative for the perfect form.  It
    # also corrects a few known source-dataset typos (for example *beteilig).
    headword_text = re.sub(r"([a-zäöüß])-\s+([a-zäöüß])", r"\1\2", source_text.lower())
    official_perfect_matches = re.findall(
        r"\b(hat/ist|ist/hat|hat|ist)\s+(?:sich\s+)?([a-zäöüß]+)",
        headword_text,
    )
    if official_perfect_matches and lemma not in MANUAL_FORMS:
        participle = official_perfect_matches[-1][1]

    if mandatory_reflexive:
        base_present = present[:]
        reflexive_pronouns = ("mich", "dich", "sich", "uns", "euch", "sich")
        present = [insert_reflexive(form, pronoun) for form, pronoun in zip(present, reflexive_pronouns)]
        past = [insert_reflexive(form, pronoun) for form, pronoun in zip(past, reflexive_pronouns)]
        imperative = [
            f"{insert_reflexive(imp_sg, 'dich')}!",
            insert_subject(base_present[3], "wir", "uns"),
            f"{insert_reflexive(imp_pl, 'euch')}!",
            insert_subject(base_present[5], "Sie", "sich"),
        ]
        participle = f"sich {participle}"
    else:
        imperative = [
            finite_imperative(imp_sg, "du"),
            insert_subject(present[3], "wir"),
            finite_imperative(imp_pl, "ihr"),
            insert_subject(present[5], "Sie"),
        ]

    sein_verbs = {
        "abbiegen", "abfahren", "ankommen", "auffallen", "aufstehen",
        "auftreten", "aufwachen", "ausfallen", "ausgehen", "begegnen",
        "einbrechen", "einfallen", "einsteigen", "eintreten", "einziehen",
        "erschrecken", "feststehen", "fließen", "gelingen", "geschehen", "losfahren", "reiten", "rennen",
        "schwimmen", "sinken", "spazierengehen", "springen", "sterben",
        "stürzen", "umgehen", "umsteigen", "verreisen", "vorkommen", "wachsen",
        "wandern", "zugehen", "zurechtkommen",
    }
    dual_auxiliary_verbs = {"ausziehen", "eilen", "liegen", "tauchen", "trocknen", "umziehen"}
    auxiliary = "sein" if lemma in sein_verbs else "haben"
    if lemma in dual_auxiliary_verbs:
        auxiliary = "haben / sein"
    if lemma == "umziehen":
        auxiliary = "haben / sein"
        display = "umziehen / sich umziehen"
        infinitive = display

    separable = " " in present[0] and not mandatory_reflexive
    kind = verb_type(past[0], participle, separable)
    gloss = translations[lemma]
    if not gloss.startswith("to "):
        gloss = "to " + gloss

    entry = (
        f"\\BOneVerb{{{display}}}{{{infinitive}}}{{{gloss}}}{{{kind}}}{{{auxiliary}}}"
        f"{{{','.join(present)}}}{{{','.join(past)}}}"
        f"{{{','.join(imperative)}}}{{{participle}}}\n"
    )
    letter = lemma[0].translate(str.maketrans({"ä": "a", "ö": "o", "ü": "u"}))
    by_letter[letter].append(entry)

for letter, entries in by_letter.items():
    content = "% Official Goethe-Zertifikat B1 vocabulary additions.\n"
    content += "\\subsection*{Additional B1 verbs}\n\n"
    content += "\n".join(entries)
    (args.out / f"{letter}.tex").write_text(content, encoding="utf-8")

print(f"Generated {sum(map(len, by_letter.values()))} entries in {len(by_letter)} letter files")
