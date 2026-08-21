import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sdd1 import decoder
from sdd1.probability import MAX_LENGTH

VECTORS = json.loads((ROOT / "conformance" / "vectors.json").read_text())
BLOB = bytes.fromhex(VECTORS["input"])


class BitplaneTest(unittest.TestCase):
    def test_each_type_names_how_many_planes_it_interleaves(self) -> None:
        self.assertEqual(
            [decoder.bitplane_count(kind) for kind in range(4)],
            [2, 4, 4, 8],
        )


class HeaderTest(unittest.TestCase):
    def test_a_stream_shorter_than_its_header_is_refused(self) -> None:
        with self.assertRaises(decoder.TruncatedStream):
            decoder.decompress(b"\x00", 0, 16)

    def test_an_offset_past_the_end_is_refused(self) -> None:
        with self.assertRaises(decoder.TruncatedStream):
            decoder.decompress(b"\x00\x00", 5, 16)

    def test_a_negative_offset_is_refused(self) -> None:
        with self.assertRaises(decoder.TruncatedStream):
            decoder.decompress(b"\x00\x00", -1, 16)

    def test_a_stream_that_runs_out_mid_decode_is_refused(self) -> None:
        with self.assertRaises(decoder.TruncatedStream):
            decoder.decompress(bytes([0xFF, 0xFF]), 0, 0x1000)

    def test_the_header_decides_how_many_planes_are_reported(self) -> None:
        found = decoder.decompress(bytes([0xC0]) + BLOB[:64], 0, 8)

        self.assertEqual(found.bitplanes, 8)

    def test_the_header_decides_which_context_masks_are_used(self) -> None:
        found = decoder.decompress(bytes([0x30]) + BLOB[:64], 0, 8)

        self.assertEqual(found.context, 3)


class LengthTest(unittest.TestCase):
    def test_a_stream_gives_back_the_length_asked_for(self) -> None:
        for length in (1, 2, 3, 15, 16, 17, 64, 833):
            found = decoder.decompress(BLOB, 0, length)

            self.assertEqual(len(found.data), length)

    def test_a_length_of_zero_means_one_whole_block(self) -> None:
        found = decoder.decompress(BLOB, 0, 0)

        self.assertEqual(len(found.data), MAX_LENGTH)

    def test_a_stream_reports_where_it_stopped_reading(self) -> None:
        found = decoder.decompress(BLOB, 0, 64)

        self.assertGreater(found.end, 2)
        self.assertLessEqual(found.end, len(BLOB))

    def test_a_longer_read_consumes_at_least_as_much_stream(self) -> None:
        short = decoder.decompress(BLOB, 0, 16)
        long = decoder.decompress(BLOB, 0, 256)

        self.assertGreaterEqual(long.end, short.end)


class DeterminismTest(unittest.TestCase):
    def test_the_same_stream_decodes_the_same_way_twice(self) -> None:
        self.assertEqual(
            decoder.decompress(BLOB, 100, 256).data,
            decoder.decompress(BLOB, 100, 256).data,
        )

    def test_a_shorter_read_is_a_prefix_of_a_longer_one(self) -> None:
        short = decoder.decompress(BLOB, 100, 64).data
        long = decoder.decompress(BLOB, 100, 256).data

        self.assertEqual(long[:64], short)

    def test_a_different_offset_decodes_differently(self) -> None:
        self.assertNotEqual(
            decoder.decompress(BLOB, 100, 64).data,
            decoder.decompress(BLOB, 200, 64).data,
        )


class EveryHeaderTest(unittest.TestCase):
    def test_every_combination_of_plane_and_context_type_decodes(self) -> None:
        for bitplane_type in range(4):
            for context_type in range(4):
                header = (bitplane_type << 6) | (context_type << 4)
                payload = bytes([header]) + BLOB[:4096]

                with self.subTest(planes=bitplane_type, context=context_type):
                    found = decoder.decompress(payload, 0, 128)

                    self.assertEqual(len(found.data), 128)
                    self.assertEqual(found.context, context_type)

    def test_every_plane_type_reports_its_own_plane_count(self) -> None:
        for bitplane_type in range(4):
            payload = bytes([bitplane_type << 6]) + BLOB[:4096]

            found = decoder.decompress(payload, 0, 64)

            self.assertEqual(found.bitplanes, decoder.bitplane_count(bitplane_type))


if __name__ == "__main__":
    unittest.main()
