"""That the record of the independent encoder run says what a reader needs.

The run itself needs twenty files this repository does not carry, so it cannot
happen here. What can happen here is holding the record to its own shape: that
every pair names both halves by digest, that the counts add up to the pairs
listed, and that a pair the decoder did not reproduce says so rather than being
quietly dropped. A record whose totals do not match its rows is worse than no
record, because it reads as a measurement.
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

independent = importlib.import_module("independent")

DIGESTS = ("crc32", "md5", "sha1", "sha256")

WIDTHS = {"crc32": 8, "md5": 32, "sha1": 40, "sha256": 64}


class RecordTest(unittest.TestCase):
    def held(self) -> dict[str, Any]:
        found = independent.recorded()
        assert isinstance(found, dict)
        return found

    def test_the_record_says_when_it_was_measured(self) -> None:
        self.assertTrue(self.held()["measuredOn"])

    def test_it_carries_no_bytes_of_anything(self) -> None:
        text = json.dumps(self.held())

        self.assertNotIn("data", text.split('"pairs"')[0].lower().replace("dated", ""))

    def test_the_source_is_named_and_not_carried(self) -> None:
        source = self.held()["source"]

        self.assertEqual((bool(source["author"]), source["carried"]), (True, False))

    def test_and_says_how_to_repeat_it(self) -> None:
        self.assertIn("Source/sdd1", self.held()["source"]["howToRepeat"])

    def test_every_pair_names_both_halves_by_every_digest(self) -> None:
        missing = [
            (one["name"], half, key)
            for one in self.held()["pairs"]
            for half in ("compressed", "declared")
            for key in DIGESTS
            if key not in one[half]
        ]

        self.assertEqual(missing, [])

    def test_every_digest_is_the_width_it_should_be(self) -> None:
        wrong = [
            (one["name"], half, key)
            for one in self.held()["pairs"]
            for half in ("compressed", "declared")
            for key, width in WIDTHS.items()
            if len(str(one[half][key])) != width
        ]

        self.assertEqual(wrong, [])

    def test_the_two_halves_of_a_pair_are_different_files(self) -> None:
        same = [
            one["name"]
            for one in self.held()["pairs"]
            if one["compressed"]["sha256"] == one["declared"]["sha256"]
        ]

        self.assertEqual(same, [])

    def test_the_counts_add_up_to_the_pairs_listed(self) -> None:
        held = self.held()
        counted = held["reproduced"] + held["shortByAuthor"] + held["differs"]

        self.assertEqual(counted, len(held["pairs"]))

    def test_every_outcome_is_one_the_record_counts(self) -> None:
        stray = [
            one["name"]
            for one in self.held()["pairs"]
            if one["outcome"] not in ("identical", "shortByAuthor", "differs")
        ]

        self.assertEqual(stray, [])

    def test_a_pair_that_was_reproduced_produced_everything_it_declared(self) -> None:
        wrong = [
            one["name"]
            for one in self.held()["pairs"]
            if one["outcome"] == "identical" and one["reproduced"] != one["declaredBytes"]
        ]

        self.assertEqual(wrong, [])

    def test_a_short_pair_produced_less_than_it_declared(self) -> None:
        wrong = [
            one["name"]
            for one in self.held()["pairs"]
            if one["outcome"] == "shortByAuthor" and one["reproduced"] >= one["declaredBytes"]
        ]

        self.assertEqual(wrong, [])

    def test_the_short_ones_are_explained_rather_than_left_standing(self) -> None:
        held = self.held()

        self.assertEqual(bool(held["aboutTheShortOnes"]), held["shortByAuthor"] > 0)

    def test_the_explanation_says_the_shortfall_is_not_this_decoder(self) -> None:
        self.assertIn("author's own export", self.held()["aboutTheShortOnes"])

    def test_no_pair_was_corrected_to_make_the_run_agree(self) -> None:
        self.assertIn("correcting somebody else's file", self.held()["aboutTheShortOnes"])

    def test_more_pairs_were_reproduced_than_were_not(self) -> None:
        held = self.held()

        self.assertGreater(held["reproduced"], held["shortByAuthor"] + held["differs"])


class AuthoredTest(unittest.TestCase):
    """The seven streams that ship with nothing beside them, and the control among them.

    The twenty pairs are a round trip inside one toolchain. One of these is an
    unmodified export of data the retail cartridge also holds, so decoding it
    here and decoding the cartridge here have to reach the same bytes. Its
    modified siblings have to not, or the comparison was measuring nothing.
    """

    def held(self) -> dict[str, Any]:
        found = independent.recorded()["authored"]
        assert isinstance(found, dict)
        return found

    def test_the_section_says_why_it_is_not_the_pairs_again(self) -> None:
        self.assertIn("round trip inside one toolchain", self.held()["why"])

    def test_every_stream_names_both_halves_by_every_digest(self) -> None:
        missing = [
            (one["name"], half, key)
            for one in self.held()["streams"]
            for half in ("compressed", "expanded")
            for key in DIGESTS
            if key not in one[half]
        ]

        self.assertEqual(missing, [])

    def test_every_digest_is_the_width_it_should_be(self) -> None:
        wrong = [
            (one["name"], half, key)
            for one in self.held()["streams"]
            for half in ("compressed", "expanded")
            for key, width in WIDTHS.items()
            if len(str(one[half][key])) != width
        ]

        self.assertEqual(wrong, [])

    def test_exactly_one_stream_is_the_positive_control(self) -> None:
        matched = [one["name"] for one in self.held()["streams"] if one["matchesRetail"]]

        self.assertEqual(matched, [self.held()["positiveControl"]["name"]])

    def test_the_control_names_where_in_the_cartridge_it_matched(self) -> None:
        self.assertTrue(self.held()["positiveControl"]["retailStreamAt"])

    def test_it_agreed_over_every_byte_the_export_carries(self) -> None:
        control = self.held()["positiveControl"]

        self.assertEqual(
            control["agreedBytes"] + control["shortByAuthor"], control["retailDeclaredBytes"]
        )

    def test_the_negative_control_is_the_same_screen_with_names_changed(self) -> None:
        self.assertIn("names changed", self.held()["negativeControl"]["why"])

    def test_and_none_of_those_matched_anything(self) -> None:
        names = set(self.held()["negativeControl"]["names"])
        matched = {one["name"] for one in self.held()["streams"] if one["matchesRetail"]}

        self.assertEqual(names & matched, set())

    def test_there_are_more_negative_controls_than_positive(self) -> None:
        self.assertGreater(len(self.held()["negativeControl"]["names"]), 1)

    def test_the_search_says_how_wide_it_was(self) -> None:
        self.assertIn("Every stream in both cartridges", self.held()["searched"])

    def test_the_shortfall_is_the_authors_rather_than_corrected(self) -> None:
        self.assertIn("left uncorrected", self.held()["aboutTheShortOne"])

    def test_a_stream_that_never_runs_out_says_so(self) -> None:
        endless = [one["name"] for one in self.held()["streams"] if one["runsOn"]]

        self.assertEqual(endless, ["7e9440 table"])

    def test_every_stream_expanded_to_something(self) -> None:
        empty = [one["name"] for one in self.held()["streams"] if one["expandedBytes"] <= 0]

        self.assertEqual(empty, [])


class CountingTest(unittest.TestCase):
    def test_a_run_with_nothing_in_it_counts_nothing(self) -> None:
        self.assertEqual(independent.tally([]), {"identical": 0, "shortByAuthor": 0, "differs": 0})

    def test_each_outcome_is_counted_under_its_own_name(self) -> None:
        rows = [{"outcome": "identical"}, {"outcome": "identical"}, {"outcome": "differs"}]

        self.assertEqual(
            independent.tally(rows), {"identical": 2, "shortByAuthor": 0, "differs": 1}
        )

    def test_an_outcome_nobody_named_is_not_silently_counted(self) -> None:
        self.assertEqual(independent.tally([{"outcome": "maybe"}])["identical"], 0)


if __name__ == "__main__":
    unittest.main()
