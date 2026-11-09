import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verb_data import (  # noqa: E402
    OUTPUT_FILE,
    PERSONS,
    VERB_TYPES,
    ValidationError,
    iter_verbs,
    load_document,
    render_document,
    validate_document,
)


class VerbCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_document()
        cls.verbs = list(iter_verbs(cls.document))

    def test_expected_catalogue_size(self):
        self.assertEqual(len(self.verbs), 635)
        compounds = sum(len(verb["separable_compounds"]) for verb in self.verbs)
        prepositional_uses = sum(len(verb["prepositional_uses"]) for verb in self.verbs)
        self.assertEqual(compounds, 334)
        self.assertEqual(prepositional_uses, 479)

    def test_every_conjugation_has_all_persons(self):
        for verb in self.verbs:
            conjugation = verb["conjugation"]
            self.assertEqual(tuple(conjugation["present"]), PERSONS)
            self.assertEqual(tuple(conjugation["preterite"]), PERSONS)
            if conjugation["subjunctive_ii"] is not None:
                self.assertEqual(tuple(conjugation["subjunctive_ii"]), PERSONS)

    def test_types_use_the_standard_vocabulary(self):
        used_types = {verb["grammar"]["type"] for verb in self.verbs}
        self.assertEqual(used_types, VERB_TYPES)

    def test_colours_cover_explicit_object_cases(self):
        cases_by_style = {
            "default": set(), "nom": set(), "modal": set(),
            "acc": {"accusative"}, "dat": {"dative"},
            "accdat": {"accusative", "dative"}, "gen": {"genitive"},
        }
        for verb in self.verbs:
            cases = cases_by_style[verb["grammar"]["style"]]
            for use in verb["prepositional_uses"]:
                for pattern in use["patterns"]:
                    # A bare lemma denotes direct government. Cases after a
                    # preposition must not determine the table background.
                    if pattern["phrase"] == verb["lemma"]:
                        with self.subTest(verb=verb["lemma"]):
                            self.assertLessEqual(set(pattern["government"]), cases)
            if verb["lemma"].startswith("sich "):
                ich = verb["conjugation"]["present"]["ich"].split()
                with self.subTest(verb=verb["lemma"], reflexive=True):
                    if "mich" in ich:
                        self.assertIn("accusative", cases)
                    elif "mir" in ich:
                        self.assertIn("dative", cases)
                    elif ich == ["-"]:
                        self.assertIn("sich", verb["conjugation"]["present"]["er_sie_es"].split())
                        self.assertIn("accusative", cases)
                    else:
                        self.fail("reflexive entry needs mich or mir in its ich form")

    def test_object_colour_regressions(self):
        by_lemma = {verb["lemma"]: verb for verb in self.verbs}
        expected = {
            "besuchen": "acc", "reparieren": "acc", "kaufen": "acc",
            "danken": "dat", "vertrauen": "dat", "gratulieren": "dat",
            "geben": "accdat", "verkaufen": "accdat", "erklären": "accdat",
            "sich merken": "accdat", "sich nähern": "accdat",
            "sich erinnern": "acc", "sich bedanken": "acc",
            "reagieren": "default", "stimmen": "default",
            "erschrecken (intransitive)": "default",
            "erschrecken (transitive)": "acc",
        }
        for lemma, style in expected.items():
            with self.subTest(verb=lemma):
                self.assertEqual(by_lemma[lemma]["grammar"]["style"], style)

    def test_unknown_colour_is_rejected(self):
        invalid = copy.deepcopy(self.document)
        invalid["chapters"][0]["groups"][0]["verbs"][0]["grammar"]["style"] = "blue"
        with self.assertRaisesRegex(ValidationError, "style is not recognized"):
            validate_document(invalid)

    def test_new_separable_and_inseparable_forms(self):
        by_lemma = {verb["lemma"]: verb for verb in self.verbs}
        expected = {
            # The stem changes, prefix placement and participles need separate
            # editorial checks; they cannot be inferred from spelling alone.
            "festnehmen": ("nimmst fest", "nahm fest", "festgenommen"),
            "festhalten": ("hältst fest", "hielt fest", "festgehalten"),
            "freilassen": ("lässt frei", "ließ frei", "freigelassen"),
            "vorschreiben": ("schreibst vor", "schrieb vor", "vorgeschrieben"),
            "übergeben": ("übergibst", "übergab", "übergeben"),
            "überreichen": ("überreichst", "überreichte", "überreicht"),
            "inhaftieren": ("inhaftierst", "inhaftierte", "inhaftiert"),
        }
        for lemma, (present_du, past_er, participle) in expected.items():
            verb = by_lemma[lemma]
            with self.subTest(verb=lemma):
                self.assertEqual(verb["conjugation"]["present"]["du"], present_du)
                self.assertEqual(verb["conjugation"]["preterite"]["er_sie_es"], past_er)
                self.assertEqual(verb["compound_tenses"]["perfect"]["form"], participle)
        self.assertEqual(
            by_lemma["sich anspannen"]["conjugation"]["imperative"]["du"],
            "spann(e) (du) dich an!",
        )
        self.assertEqual(
            by_lemma["sich verabschieden"]["conjugation"]["present"]["ich"],
            "verabschiede mich",
        )
        self.assertTrue(by_lemma["sich übergeben"]["compound_tenses"]["perfect"]["reflexive"])
        self.assertIsNone(by_lemma["sich übergeben"]["conjugation"]["imperative"])

    def test_besichtigen_and_besitzen_have_distinct_participles(self):
        by_lemma = {verb["lemma"]: verb for verb in self.verbs}
        for lemma, participle in (("besichtigen", "besichtigt"), ("besitzen", "besessen")):
            for tense in ("perfect", "pluperfect"):
                with self.subTest(verb=lemma, tense=tense):
                    self.assertEqual(by_lemma[lemma]["compound_tenses"][tense]["form"], participle)

    def test_duplicate_headword_is_rejected(self):
        invalid = copy.deepcopy(self.document)
        first_group = invalid["chapters"][0]["groups"][0]
        first_group["verbs"][1]["lemma"] = first_group["verbs"][0]["lemma"]
        with self.assertRaisesRegex(ValidationError, "duplicate verb headword"):
            validate_document(invalid)

    def test_meanings_with_different_prefixes_and_past_forms(self):
        by_lemma = {verb["lemma"]: verb for verb in self.verbs}
        expected = {
            "übernehmen": ("übernimmt", "übernahm", "übernommen"),
            "überfliegen": ("überfliegt", "überflog", "überflogen"),
            "staubsaugen": ("staubsaugt", "staubsaugte", "gestaubsaugt"),
            "spazieren gehen": ("geht spazieren", "ging spazieren", "spazieren gegangen"),
            "ahmen": ("ahmt", "ahmte", "geahmt"),
            "schaffen (create)": ("schafft", "schuf", "geschaffen"),
            "schaffen (manage)": ("schafft", "schaffte", "geschafft"),
        }
        for lemma, (present, past, participle) in expected.items():
            verb = by_lemma[lemma]
            with self.subTest(verb=lemma):
                self.assertEqual(verb["conjugation"]["present"]["er_sie_es"], present)
                self.assertEqual(verb["conjugation"]["preterite"]["er_sie_es"], past)
                self.assertEqual(verb["compound_tenses"]["perfect"]["form"], participle)
        self.assertEqual(by_lemma["arbeiten"]["conjugation"]["imperative"]["du"], "arbeite (du)!")
        self.assertEqual(by_lemma["sich treffen"]["conjugation"]["imperative"]["du"], "triff (du) dich!")

    def test_inconsistent_compound_tenses_are_rejected(self):
        corruptions = [
            ("perfect", "form", "besessen", "participles differ"),
            ("perfect", "auxiliaries", ["haben"], "auxiliaries differ"),
            ("pluperfect", "auxiliaries", ["hatten"], "pluperfect auxiliaries"),
            ("future", "form", "besitzen", "differs from infinitive"),
            ("future", "reflexive", True, "inconsistent reflexive"),
        ]
        for tense, field, value, message in corruptions:
            invalid = copy.deepcopy(self.document)
            invalid["chapters"][0]["groups"][0]["verbs"][0]["compound_tenses"][tense][field] = value
            with self.subTest(tense=tense, field=field):
                with self.assertRaisesRegex(ValidationError, message):
                    validate_document(invalid)

    def test_missing_person_is_rejected(self):
        invalid = copy.deepcopy(self.document)
        del invalid["chapters"][0]["groups"][0]["verbs"][0]["conjugation"]["present"]["ihr"]
        with self.assertRaisesRegex(ValidationError, "fields differ from schema"):
            validate_document(invalid)

    def test_generated_latex_is_current(self):
        self.assertEqual(OUTPUT_FILE.read_text(encoding="utf-8"), render_document(self.document))


if __name__ == "__main__":
    unittest.main()
