import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sdd1

HISTORY_BITS = 10

HISTORY = (1 << HISTORY_BITS) - 1

LIKELY = 1

UNLIKELY = 2


def settles(start: int, which: int) -> bool:
    seen: list[int] = []
    state = start
    while state not in seen:
        seen = [*seen, state]
        state = sdd1.EVOLUTION[state][which]
    return bool(sdd1.EVOLUTION[state][which] == state)


class EvolutionTest(unittest.TestCase):
    def test_every_state_names_a_code_size_and_two_successors(self) -> None:
        # Arrange
        table = sdd1.EVOLUTION

        # Act
        widths = {len(row) for row in table}

        # Assert
        self.assertEqual(widths, {3})

    def test_every_successor_is_a_state_that_exists(self) -> None:
        # Arrange
        states = range(len(sdd1.EVOLUTION))

        # Act
        stray = [
            row
            for row in sdd1.EVOLUTION
            if row[LIKELY] not in states or row[UNLIKELY] not in states
        ]

        # Assert
        self.assertEqual(stray, [])

    def test_every_code_size_fits_the_run_table(self) -> None:
        # Arrange
        sizes = range(8)

        # Act
        stray = [code_size for code_size, _, _ in sdd1.EVOLUTION if code_size not in sizes]

        # Assert
        self.assertEqual(stray, [])

    def test_following_the_likely_symbol_always_settles(self) -> None:
        # Arrange
        starts = range(len(sdd1.EVOLUTION))

        # Act
        unsettled = [start for start in starts if not settles(start, LIKELY)]

        # Assert
        self.assertEqual(unsettled, [])

    def test_following_the_unlikely_symbol_always_settles(self) -> None:
        # Arrange
        starts = range(len(sdd1.EVOLUTION))

        # Act
        unsettled = [start for start in starts if not settles(start, UNLIKELY)]

        # Assert
        self.assertEqual(unsettled, [])


class RunTableTest(unittest.TestCase):
    def test_the_table_is_indexed_by_seven_bits(self) -> None:
        # Arrange
        table = sdd1.RUN_TABLE

        # Act
        size = len(table)

        # Assert
        self.assertEqual(size, 128)

    def test_the_table_is_a_permutation_of_every_run_length_it_can_give(self) -> None:
        # Arrange
        table = sdd1.RUN_TABLE

        # Act
        found = sorted(table)

        # Assert
        self.assertEqual(found, list(range(1, 129)))

    def test_the_longest_run_comes_first(self) -> None:
        # Arrange
        table = sdd1.RUN_TABLE

        # Act
        first = table[0]

        # Assert
        self.assertEqual(first, 128)


class ContextMaskTest(unittest.TestCase):
    def test_there_is_a_mask_pair_for_every_context_type(self) -> None:
        # Arrange
        masks = sdd1.CONTEXT_MASKS

        # Act
        count = len(masks)

        # Assert
        self.assertEqual(count, 4)

    def test_every_mask_fits_the_history_that_is_kept(self) -> None:
        # Arrange
        masks = sdd1.CONTEXT_MASKS

        # Act
        stray = [pair for pair in masks if (pair[0] | pair[1]) & ~HISTORY]

        # Assert
        self.assertEqual(stray, [])

    def test_no_mask_pair_selects_the_same_bit_twice(self) -> None:
        # Arrange
        masks = sdd1.CONTEXT_MASKS

        # Act
        overlapping = [(high, low) for high, low in masks if high & low]

        # Assert
        self.assertEqual(overlapping, [])

    def test_every_mask_pair_stays_inside_the_context_count(self) -> None:
        # Arrange
        masks = sdd1.CONTEXT_MASKS

        # Act
        widest = [((high & HISTORY) >> 5) | low for high, low in masks]

        # Assert
        self.assertEqual([one for one in widest if one >= sdd1.CONTEXT_COUNT], [])


class SizeTest(unittest.TestCase):
    def test_the_chip_keeps_one_context_set_of_thirty_two(self) -> None:
        # Arrange
        model = sdd1.MODELS["sdd1"]

        # Act
        found = (sdd1.CONTEXT_COUNT, model.contexts)

        # Assert
        self.assertEqual(found, (32, 32))

    def test_the_chip_interleaves_at_most_eight_planes(self) -> None:
        # Arrange
        widest = bytes([0xC0]) + bytes(64)

        # Act
        found = sdd1.decompress(widest, 0, 8).bitplanes

        # Assert
        self.assertEqual((sdd1.PLANE_COUNT, found), (8, 8))

    def test_a_block_is_sixty_four_kilobytes(self) -> None:
        # Arrange
        quiet = bytes(4096)

        # Act
        found = len(sdd1.decompress(quiet, 0, 0).data)

        # Assert
        self.assertEqual((sdd1.MAX_LENGTH, found), (0x10000, 0x10000))


if __name__ == "__main__":
    unittest.main()
