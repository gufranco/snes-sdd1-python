"""That the prototype record says what a reader needs and claims no more.

The run itself needs two cartridges this repository does not carry, so it cannot
happen here. What can happen here is holding the record to its own shape: that
both cartridges are identified, that every match names where it was found and
what it expanded to, that the counts add up to the streams decoded, and that a
match which could not be placed says so rather than being written down as though
it had been. A record whose totals do not match its rows reads as a measurement
and is not one.
"""

import importlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "conformance"))

prototype = importlib.import_module("prototype")

DIGESTS = ("crc32", "md5", "sha1", "sha256")

WIDTHS = {"crc32": 8, "md5": 32, "sha1": 40, "sha256": 64}


class RecordTest(unittest.TestCase):
    def held(self) -> dict[str, Any]:
        found = prototype.recorded()
        assert isinstance(found, dict)
        return found

    def test_the_record_says_when_it_was_measured(self) -> None:
        self.assertTrue(self.held()["measuredOn"])

    def test_it_says_which_rung_of_the_ladder_this_is(self) -> None:
        self.assertEqual(self.held()["rung"], prototype.RUNG)

    def test_and_why_that_rung_rather_than_a_higher_one(self) -> None:
        self.assertIn("not a document", self.held()["aboutTheRung"])

    def test_it_says_why_this_witness_is_not_the_others_again(self) -> None:
        self.assertIn("predates the compression", self.held()["note"])

    def test_both_cartridges_are_identified_by_every_digest(self) -> None:
        missing = [
            (which, key)
            for which in ("final", "prototype")
            for key in DIGESTS
            if key not in self.held()["cartridges"][which]
        ]

        self.assertEqual(missing, [])

    def test_every_cartridge_digest_is_the_width_it_should_be(self) -> None:
        wrong = [
            (which, key)
            for which in ("final", "prototype")
            for key, width in WIDTHS.items()
            if len(str(self.held()["cartridges"][which][key])) != width
        ]

        self.assertEqual(wrong, [])

    def test_the_two_cartridges_are_different_files(self) -> None:
        held = self.held()["cartridges"]

        self.assertNotEqual(held["final"]["sha256"], held["prototype"]["sha256"])

    def test_neither_cartridge_is_carried_here(self) -> None:
        present = [p.name for p in ROOT.rglob("*.sfc")]

        self.assertEqual(present, [])

    def test_the_counts_add_up_to_the_streams_decoded(self) -> None:
        held = self.held()
        counted = held["matchedInFull"] + held["prefixOnly"] + held["absent"]

        self.assertEqual(counted, held["decoded"])

    def test_the_matched_count_is_the_number_of_rows(self) -> None:
        held = self.held()

        self.assertEqual(held["matchedInFull"], len(held["matches"]))

    def test_every_match_names_the_stream_it_came_from(self) -> None:
        silent = [one for one in self.held()["matches"] if not one.get("streamAt")]

        self.assertEqual(silent, [])

    def test_every_match_names_where_it_was_found(self) -> None:
        silent = [one["streamAt"] for one in self.held()["matches"] if not one.get("protoAt")]

        self.assertEqual(silent, [])

    def test_every_match_carries_a_digest_of_what_it_expanded_to(self) -> None:
        wrong = [
            one["streamAt"]
            for one in self.held()["matches"]
            if len(str(one.get("expanded", ""))) != WIDTHS["sha256"]
        ]

        self.assertEqual(wrong, [])

    def test_no_match_is_shorter_than_the_length_a_prefix_would_reach(self) -> None:
        short = [one["streamAt"] for one in self.held()["matches"] if one["declaredBytes"] < 64]

        self.assertEqual(short, [])

    def test_the_bytes_confirmed_are_the_sum_of_the_matches(self) -> None:
        held = self.held()

        self.assertEqual(held["bytesConfirmed"], prototype.confirmed(held["matches"]))

    def test_an_ambiguous_match_says_so_rather_than_naming_one_place(self) -> None:
        held = self.held()
        placed = prototype.located(held["matches"])

        self.assertEqual(len(held["matches"]) - len(placed), 2)

    def test_and_the_record_explains_why_those_are_kept(self) -> None:
        self.assertIn("confirmed either way", self.held()["aboutTheAmbiguousTwo"])

    def test_a_miss_is_explained_rather_than_left_as_a_failure(self) -> None:
        self.assertIn("different build", self.held()["aboutTheMisses"])

    def test_and_a_prefix_is_not_counted_as_a_match(self) -> None:
        self.assertIn("full match is required", self.held()["aboutTheMisses"])

    def test_more_streams_were_decoded_than_matched(self) -> None:
        held = self.held()

        self.assertGreater(held["decoded"], held["matchedInFull"])

    def test_every_stream_offered_decoded_without_error(self) -> None:
        held = self.held()

        self.assertNotIn("failedToDecode", held)

    def test_the_record_says_how_to_repeat_it(self) -> None:
        self.assertIn("search the prototype", self.held()["howToRepeat"])

    def test_it_carries_no_bytes_of_either_cartridge(self) -> None:
        text = json.dumps(self.held())

        self.assertNotIn("base64", text.lower())


class HelpersTest(unittest.TestCase):
    def test_nothing_matched_confirms_nothing(self) -> None:
        self.assertEqual(prototype.confirmed([]), 0)

    def test_the_confirmed_bytes_are_the_declared_lengths_added_up(self) -> None:
        rows = [{"declaredBytes": 10}, {"declaredBytes": 32}]

        self.assertEqual(prototype.confirmed(rows), 42)

    def test_a_placed_match_is_located(self) -> None:
        rows = [{"streamAt": "0x01", "protoAt": "0x99"}]

        self.assertEqual(prototype.located(rows), ["0x01"])

    def test_an_ambiguous_one_is_not(self) -> None:
        rows = [{"streamAt": "0x01", "protoAt": prototype.AMBIGUOUS}]

        self.assertEqual(prototype.located(rows), [])


if __name__ == "__main__":
    unittest.main()
