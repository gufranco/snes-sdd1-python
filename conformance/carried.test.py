import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sdd1  # noqa: E402

HELD: dict[str, Any] = json.loads((ROOT / "conformance" / "carried.json").read_text())

FACTS: dict[str, Any] = json.loads((ROOT / "conformance" / "hardware.json").read_text())["facts"]


def digest_of(values: Any) -> str:
    return hashlib.sha256(json.dumps(list(values), separators=(",", ":")).encode()).hexdigest()


class CarriedTableTest(unittest.TestCase):
    @property
    def entries(self) -> list[dict[str, Any]]:
        held: list[dict[str, Any]] = HELD["tables"]
        return held

    def test_every_pinned_table_is_the_table_that_was_pinned(self) -> None:
        # Arrange
        entries = self.entries

        # Act
        wrong = [
            entry["name"]
            for entry in entries
            if digest_of(getattr(sdd1, entry["name"])) != entry["sha256"]
        ]

        # Assert
        self.assertEqual(wrong, [])

    def test_every_pinned_table_is_the_length_that_was_pinned(self) -> None:
        # Arrange
        entries = self.entries

        # Act
        wrong = [
            entry["name"]
            for entry in entries
            if len(getattr(sdd1, entry["name"])) != entry["entries"]
        ]

        # Assert
        self.assertEqual(wrong, [])

    def test_a_changed_entry_is_caught(self) -> None:
        # Arrange
        held = getattr(sdd1, self.entries[0]["name"])

        # Act
        bent = ["changed", *list(held)[1:]]

        # Assert
        self.assertNotEqual(digest_of(bent), digest_of(held))

    def test_a_reordering_that_keeps_the_same_values_is_caught(self) -> None:
        # Arrange
        held = list(getattr(sdd1, self.entries[0]["name"]))

        # Act
        swapped = [held[-1], *held[1:-1], held[0]]

        # Assert
        self.assertNotEqual(digest_of(swapped), digest_of(held))

    def test_every_table_the_package_exports_is_pinned_or_recorded_as_a_fact(self) -> None:
        # Arrange
        pinned = {entry["name"] for entry in self.entries}
        recorded = [fact["value"] for fact in FACTS.values()]

        # Act
        unaccounted = {
            name
            for name in sdd1.__all__
            if name.isupper()
            and isinstance(getattr(sdd1, name), tuple)
            and name not in pinned
            and list(getattr(sdd1, name)) not in recorded
        }

        # Assert
        self.assertEqual(unaccounted, set())

    def test_the_record_says_what_a_digest_here_does_not_claim(self) -> None:
        self.assertIn("a claim that the table is correct", HELD["whatThisIsNot"].lower())

    def test_the_record_says_why_no_publisher_digest_exists(self) -> None:
        self.assertIn("publisher", HELD["notStated"])

    def test_every_table_says_what_it_is_for(self) -> None:
        silent = [entry["name"] for entry in self.entries if not entry.get("what")]

        self.assertEqual(silent, [])


if __name__ == "__main__":
    unittest.main()
