import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sdd1 import probability


class EvolutionTest(unittest.TestCase):
    def test_every_state_names_a_code_size_and_two_successors(self):
        for row in probability.EVOLUTION:
            self.assertEqual(len(row), 3)

    def test_every_successor_is_a_state_that_exists(self):
        for _, mps_next, lps_next in probability.EVOLUTION:
            self.assertIn(mps_next, range(len(probability.EVOLUTION)))
            self.assertIn(lps_next, range(len(probability.EVOLUTION)))

    def test_every_code_size_fits_the_run_table(self):
        for code_size, _, _ in probability.EVOLUTION:
            self.assertIn(code_size, range(8))

    def walk(self, start, which):
        """Where a state ends up when one symbol keeps arriving.

        The states are finite and the walk never revisits one, so this always
        returns. What it returns is the first state seen twice, which for a
        settled chain is the self loop at its end.
        """
        seen = []
        state = start
        while state not in seen:
            seen.append(state)
            state = probability.EVOLUTION[state][which]
        return state

    def test_following_the_likely_symbol_always_settles(self):
        unsettled = [
            start
            for start in range(len(probability.EVOLUTION))
            if probability.EVOLUTION[self.walk(start, 1)][1] != self.walk(start, 1)
        ]

        self.assertEqual(unsettled, [])

    def test_following_the_unlikely_symbol_always_settles(self):
        unsettled = [
            start
            for start in range(len(probability.EVOLUTION))
            if probability.EVOLUTION[self.walk(start, 2)][2] != self.walk(start, 2)
        ]

        self.assertEqual(unsettled, [])


class RunTableTest(unittest.TestCase):
    def test_the_table_is_indexed_by_seven_bits(self):
        self.assertEqual(len(probability.RUN_TABLE), 128)

    def test_the_table_is_a_permutation_of_every_run_length_it_can_give(self):
        self.assertEqual(sorted(probability.RUN_TABLE), list(range(1, 129)))

    def test_the_longest_run_comes_first(self):
        self.assertEqual(probability.RUN_TABLE[0], max(probability.RUN_TABLE))


class ContextMaskTest(unittest.TestCase):
    def test_there_is_a_mask_pair_for_every_context_type(self):
        self.assertEqual(len(probability.CONTEXT_MASKS), 4)

    def test_every_mask_fits_the_history_that_is_kept(self):
        for high, low in probability.CONTEXT_MASKS:
            self.assertEqual(high & ~probability.PREV_BITS_MASK, 0)
            self.assertEqual(low & ~probability.PREV_BITS_MASK, 0)

    def test_no_mask_pair_selects_the_same_bit_twice(self):
        for high, low in probability.CONTEXT_MASKS:
            self.assertEqual(high & low, 0)

    def test_every_mask_pair_stays_inside_the_context_count(self):
        for high, low in probability.CONTEXT_MASKS:
            widest = ((high & probability.PREV_BITS_MASK) >> 5) | low
            self.assertLess(widest, probability.CONTEXT_COUNT)


class SizeTest(unittest.TestCase):
    def test_the_chip_keeps_one_context_set_of_thirty_two(self):
        self.assertEqual(probability.CONTEXT_COUNT, 32)

    def test_the_chip_interleaves_at_most_eight_planes(self):
        self.assertEqual(probability.PLANE_COUNT, 8)

    def test_a_block_is_sixty_four_kilobytes(self):
        self.assertEqual(probability.MAX_LENGTH, 0x10000)


if __name__ == "__main__":
    unittest.main()
