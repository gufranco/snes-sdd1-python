import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sdd1  # noqa: E402

VECTORS = json.loads((ROOT / "conformance" / "vectors.json").read_text())
BLOB = bytes.fromhex(VECTORS["input"])

PRINTED_PLANE_COUNTS = [2, 4, 4, 8]

ONE_BLOCK = 0x10000


class BitplaneTest(unittest.TestCase):
    def test_each_type_names_how_many_planes_it_interleaves(self) -> None:
        # Arrange
        kinds = range(4)

        # Act
        found = [sdd1.bitplane_count(kind) for kind in kinds]

        # Assert
        self.assertEqual(found, PRINTED_PLANE_COUNTS)


class HeaderTest(unittest.TestCase):
    def test_a_stream_shorter_than_its_header_is_refused(self) -> None:
        # Arrange
        rom = b"\x00"

        # Act
        with self.assertRaises(sdd1.TruncatedStream) as refused:
            sdd1.decompress(rom, 0, 16)

        # Assert
        self.assertEqual(refused.exception.args, (0,))

    def test_an_offset_past_the_end_is_refused(self) -> None:
        # Arrange
        rom = b"\x00\x00"

        # Act
        with self.assertRaises(sdd1.TruncatedStream) as refused:
            sdd1.decompress(rom, 5, 16)

        # Assert
        self.assertEqual(refused.exception.args, (5,))

    def test_a_negative_offset_is_refused(self) -> None:
        # Arrange
        rom = b"\x00\x00"

        # Act
        with self.assertRaises(sdd1.TruncatedStream) as refused:
            sdd1.decompress(rom, -1, 16)

        # Assert
        self.assertEqual(refused.exception.args, (-1,))

    def test_a_stream_that_runs_out_mid_decode_is_refused(self) -> None:
        # Arrange
        rom = bytes([0xFF, 0xFF])

        # Act
        with self.assertRaises(sdd1.TruncatedStream) as refused:
            sdd1.decompress(rom, 0, 0x1000)

        # Assert
        self.assertEqual(refused.exception.args, (0,))

    def test_the_header_decides_how_many_planes_are_reported(self) -> None:
        # Arrange
        rom = bytes([0xC0]) + BLOB[:64]

        # Act
        found = sdd1.decompress(rom, 0, 8)

        # Assert
        self.assertEqual(found.bitplanes, 8)

    def test_the_header_decides_which_context_masks_are_used(self) -> None:
        # Arrange
        rom = bytes([0x30]) + BLOB[:64]

        # Act
        found = sdd1.decompress(rom, 0, 8)

        # Assert
        self.assertEqual(found.context, 3)


class LengthTest(unittest.TestCase):
    def test_a_stream_gives_back_the_length_asked_for(self) -> None:
        # Arrange
        lengths = (1, 2, 3, 15, 16, 17, 64, 833)

        # Act
        found = [len(sdd1.decompress(BLOB, 0, length).data) for length in lengths]

        # Assert
        self.assertEqual(found, list(lengths))

    def test_a_length_of_zero_means_one_whole_block(self) -> None:
        # Arrange
        length = 0

        # Act
        found = sdd1.decompress(BLOB, 0, length)

        # Assert
        self.assertEqual(len(found.data), ONE_BLOCK)

    def test_a_stream_reports_where_it_stopped_reading(self) -> None:
        # Arrange
        length = 64

        # Act
        found = sdd1.decompress(BLOB, 0, length)

        # Assert
        self.assertEqual(sdd1.decompress(BLOB[: found.end], 0, length), found)
        with self.assertRaises(sdd1.TruncatedStream):
            sdd1.decompress(BLOB[: found.end - 1], 0, length)

    def test_a_longer_read_consumes_at_least_as_much_stream(self) -> None:
        # Arrange
        short = sdd1.decompress(BLOB, 0, 16)

        # Act
        long = sdd1.decompress(BLOB, 0, 256)

        # Assert
        self.assertGreaterEqual(long.end, short.end)


class DeterminismTest(unittest.TestCase):
    def test_the_same_stream_decodes_the_same_way_twice(self) -> None:
        # Arrange
        first = sdd1.decompress(BLOB, 100, 256).data

        # Act
        second = sdd1.decompress(BLOB, 100, 256).data

        # Assert
        self.assertEqual(second, first)

    def test_a_shorter_read_is_a_prefix_of_a_longer_one(self) -> None:
        # Arrange
        short = sdd1.decompress(BLOB, 100, 64).data

        # Act
        long = sdd1.decompress(BLOB, 100, 256).data

        # Assert
        self.assertEqual(long[:64], short)

    def test_a_different_offset_decodes_differently(self) -> None:
        # Arrange
        first = sdd1.decompress(BLOB, 100, 64).data

        # Act
        second = sdd1.decompress(BLOB, 200, 64).data

        # Assert
        self.assertNotEqual(second, first)


class EveryHeaderTest(unittest.TestCase):
    def test_every_combination_of_plane_and_context_type_decodes(self) -> None:
        # Arrange
        shapes = [(planes, context) for planes in range(4) for context in range(4)]

        # Act
        found = {
            (planes, context): sdd1.decompress(
                bytes([(planes << 6) | (context << 4)]) + BLOB[:4096], 0, 128
            )
            for planes, context in shapes
        }

        # Assert
        self.assertEqual(
            {shape: (len(stream.data), stream.context) for shape, stream in found.items()},
            {(planes, context): (128, context) for planes, context in shapes},
        )

    def test_every_plane_type_reports_its_own_plane_count(self) -> None:
        # Arrange
        payloads = [bytes([kind << 6]) + BLOB[:4096] for kind in range(4)]

        # Act
        found = [sdd1.decompress(payload, 0, 64).bitplanes for payload in payloads]

        # Assert
        self.assertEqual(found, PRINTED_PLANE_COUNTS)


if __name__ == "__main__":
    unittest.main()
