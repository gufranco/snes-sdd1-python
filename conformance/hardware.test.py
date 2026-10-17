import json
import sys
import unittest
from pathlib import Path
from typing import Any, override

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sdd1

HERE = Path(__file__).resolve().parent

NOISE = bytes.fromhex(json.loads((HERE / "vectors.json").read_text())["input"])[:4096]

QUIET = bytes(4096)


def declared(name: str) -> dict[str, Any]:
    held = json.loads((HERE / name).read_text())
    assert isinstance(held, dict), f"{name} does not hold an object"
    return held


class DocumentTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.declared = declared("hardware.json")

    def test_the_top_rung_of_the_ladder_is_recorded_as_empty(self) -> None:
        order = self.declared["authority"]["order"]

        self.assertIn("of which there is none", order[0])

    def test_and_the_absent_document_is_named_along_with_the_search(self) -> None:
        missing = self.declared["authority"]["whatIsMissing"]

        self.assertIn("nothing was found", missing)

    def test_no_fact_claims_to_be_documented(self) -> None:
        claimed = [name for name, fact in self.declared["facts"].items() if fact["verified"]]

        self.assertEqual(claimed, [])

    def test_every_fact_names_its_evidence_and_what_would_settle_it(self) -> None:
        missing = [
            name
            for name, fact in self.declared["facts"].items()
            if not (fact.get("evidence") and fact.get("howToSettleIt"))
        ]

        self.assertEqual(missing, [])

    def test_what_nothing_settles_is_recorded_rather_than_filled_in(self) -> None:
        stated = self.declared["notStated"]

        self.assertGreaterEqual(len(stated), 4)


class ConstantTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.facts: dict[str, Any] = declared("hardware.json")["facts"]

    def test_the_bitplane_counts_are_the_ones_declared(self) -> None:
        # Arrange
        streams = [bytes([kind << 6]) + NOISE for kind in range(4)]

        # Act
        counts = [sdd1.decompress(stream, 0, 8).bitplanes for stream in streams]

        # Assert
        self.assertEqual(counts, self.facts["bitplaneCounts"]["value"])

    def test_a_stream_begins_with_the_declared_number_of_header_bytes(self) -> None:
        # Arrange
        declared_bytes = self.facts["headerBytes"]["value"]

        # Act
        published = sdd1.HEADER_BYTES

        # Assert
        self.assertEqual(published, declared_bytes)

    def test_the_coder_keeps_the_declared_number_of_contexts(self) -> None:
        # Arrange
        model = sdd1.MODELS["sdd1"]

        # Act
        kept = {sdd1.CONTEXT_COUNT, model.contexts}

        # Assert
        self.assertEqual(kept, {self.facts["contextCount"]["value"]})

    def test_a_stream_decodes_at_most_the_declared_length(self) -> None:
        # Arrange
        longest = self.facts["maximumLength"]["value"]

        # Act
        found = len(sdd1.decompress(QUIET, 0, 0).data)

        # Assert
        self.assertEqual((found, sdd1.MAX_LENGTH), (longest, longest))

    def test_and_that_length_is_one_bank(self) -> None:
        # Arrange
        longest = self.facts["maximumLength"]["value"]

        # Act
        bank = 1 << 16

        # Assert
        self.assertEqual(longest, bank)

    def test_the_header_selects_the_declared_number_of_shapes(self) -> None:
        # Arrange
        streams = [bytes([shape << 4]) + NOISE for shape in range(16)]

        # Act
        decoded = {sdd1.decompress(stream, 0, 64).data for stream in streams}

        # Assert
        self.assertEqual(len(decoded), self.facts["headerShapes"]["value"])

    def test_every_shape_the_header_can_name_has_a_bitplane_count(self) -> None:
        # Arrange
        kinds = range(4)

        # Act
        missing = [kind for kind in kinds if sdd1.bitplane_count(kind) is None]

        # Assert
        self.assertEqual(missing, [])


class DivergenceTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.entries: list[dict[str, Any]] = declared("divergences.json")["divergences"]

    def test_each_entry_says_which_source_the_package_follows(self) -> None:
        allowed = {"document", "reference", "neither"}

        self.assertEqual({entry["packageFollows"] for entry in self.entries} - allowed, set())

    def test_each_entry_says_what_would_settle_it(self) -> None:
        missing = [entry["id"] for entry in self.entries if not entry.get("wouldSettleIt")]

        self.assertEqual(missing, [])

    def test_the_output_resting_on_an_emulator_is_recorded_as_serious(self) -> None:
        entry = next(
            item
            for item in self.entries
            if item["id"] == "every-expected-output-comes-from-an-emulator"
        )

        self.assertEqual(entry["severity"], "high")

    def test_the_census_provenance_is_recorded_with_the_measurement_behind_it(self) -> None:
        entry = next(
            item
            for item in self.entries
            if item["id"] == "the-shape-census-is-not-from-retail-cartridges"
        )

        self.assertIn("contain that tag zero", entry["reasoning"])

    def test_and_it_says_whether_the_decoder_is_affected(self) -> None:
        entry = next(
            item
            for item in self.entries
            if item["id"] == "the-shape-census-is-not-from-retail-cartridges"
        )

        self.assertIn("Not directly", entry["doesItAffectTheDecoder"])

    def test_the_absence_of_any_document_is_recorded_on_its_own(self) -> None:
        named = {entry["id"] for entry in self.entries}

        self.assertIn("no-document-exists-for-this-part", named)


if __name__ == "__main__":
    unittest.main(verbosity=1)
