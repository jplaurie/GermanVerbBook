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
        self.assertEqual(len(self.verbs), 600)
        compounds = sum(len(verb["separable_compounds"]) for verb in self.verbs)
        prepositional_uses = sum(len(verb["prepositional_uses"]) for verb in self.verbs)
        self.assertEqual(compounds, 346)
        self.assertEqual(prepositional_uses, 436)

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

    def test_duplicate_headword_is_rejected(self):
        invalid = copy.deepcopy(self.document)
        first_group = invalid["chapters"][0]["groups"][0]
        first_group["verbs"][1]["lemma"] = first_group["verbs"][0]["lemma"]
        with self.assertRaisesRegex(ValidationError, "duplicate verb headword"):
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
