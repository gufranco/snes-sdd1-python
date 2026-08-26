"""Confirming streams against a cartridge and its decompressed counterpart."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from conformance import against_cartridges as against
from sdd1.errors import TruncatedStream


class ConfirmTest(unittest.TestCase):
    def test_a_decode_whose_output_is_in_the_counterpart_is_confirmed(self) -> None:
        found = against.confirm(b"anything", b"xxHELLOxx", b"HELLO")

        self.assertEqual(found, 2)

    def test_a_decode_whose_output_is_absent_is_not(self) -> None:
        found = against.confirm(b"anything", b"xxHELLOxx", b"GOODBYE")

        self.assertIsNone(found)

    def test_a_decode_whose_output_is_already_in_the_cartridge_is_not_either(self) -> None:
        found = against.confirm(b"..HELLO..", b"xxHELLOxx", b"HELLO")

        self.assertIsNone(found)


class SweepTest(unittest.TestCase):
    def test_every_offset_in_the_span_is_tried(self) -> None:
        tried: list[int] = []

        def _noting(rom: bytes, at: int, n: int) -> bytes:
            tried.append(at)
            return b""

        against.sweep(b"\x00" * 64, b"", (0, 8), decode=_noting)

        self.assertEqual(tried, list(range(8)))

    def test_an_offset_with_no_room_for_a_stream_is_passed_over(self) -> None:
        def _refuse(rom: bytes, at: int, n: int) -> bytes:
            raise TruncatedStream(at)

        found = against.sweep(b"\x00" * 64, b"", (0, 4), decode=_refuse)

        self.assertEqual(found, [])

    def test_a_confirmed_offset_comes_back_with_where_it_landed(self) -> None:
        def _one(rom: bytes, at: int, n: int) -> bytes:
            return b"FOUND" if at == 2 else b"absent"

        found = against.sweep(b"\x00" * 64, b"..FOUND..", (0, 4), decode=_one)

        self.assertEqual([(at, where) for at, where, _ in found], [(2, 2)])

    def test_the_header_byte_of_a_confirmed_stream_is_carried(self) -> None:
        rom = bytearray(b"\x00" * 64)
        rom[2] = 0xC5

        found = against.sweep(bytes(rom), b"FOUND", (2, 3), decode=lambda r, at, n: b"FOUND")

        self.assertEqual([header for _, _, header in found], [0xC5])


class DecodeTest(unittest.TestCase):
    def test_the_default_decoder_is_this_package_s_own(self) -> None:
        stream = bytes((0x00, 0x00)) + bytes(64)

        found = against._decode(stream, 0, 8)

        self.assertEqual(len(found), 8)


class CensusTest(unittest.TestCase):
    def test_the_census_counts_how_many_were_confirmed(self) -> None:
        found = against.census([(0x10, 0x20, 0xC5), (0x30, 0x40, 0x05)], (0, 0x100))

        self.assertEqual(found["confirmed"], 2)

    def test_it_groups_them_by_the_kind_the_header_names(self) -> None:
        found = against.census([(0x10, 0x20, 0xC5), (0x30, 0x40, 0xC0)], (0, 0x100))

        self.assertEqual(found["kinds"], {"3/0": 2})

    def test_two_headers_of_different_kinds_are_counted_apart(self) -> None:
        found = against.census([(0x10, 0x20, 0xC5), (0x30, 0x40, 0x05)], (0, 0x100))

        self.assertEqual(sorted(found["kinds"]), ["0/0", "3/0"])

    def test_it_carries_no_offset_and_no_destination(self) -> None:
        found = against.census([(0x123456, 0x789ABC, 0xC5)], (0, 0x40))

        printed = json.dumps(found)

        self.assertEqual([one for one in ("123456", "789abc") if one in printed], [])

    def test_it_says_which_span_was_swept(self) -> None:
        found = against.census([], (0x100, 0x200))

        self.assertEqual(found["swept"], ["0x100", "0x200"])

    def test_a_sweep_that_confirmed_nothing_still_produces_a_census(self) -> None:
        found = against.census([], (0, 0x100))

        self.assertEqual((found["confirmed"], found["kinds"]), (0, {}))


class RecordedTest(unittest.TestCase):
    def test_the_recorded_census_names_every_kind_it_reached(self) -> None:
        found = against.recorded()

        self.assertEqual(len(found["kinds"]), 16)

    def test_it_confirmed_more_than_the_control_did(self) -> None:
        found = against.recorded()

        self.assertGreater(found["confirmed"], found["control"]["confirmed"] * 20)

    def test_it_names_the_two_files_it_was_measured_from(self) -> None:
        found = against.recorded()

        self.assertEqual([one["role"] for one in found["measuredFrom"]], ["cartridge", "expanded"])

    def test_every_file_it_names_carries_four_digests(self) -> None:
        found = against.recorded()

        for one in found["measuredFrom"]:
            self.assertEqual(
                [key for key in ("crc32", "md5", "sha1", "sha256") if key in one],
                ["crc32", "md5", "sha1", "sha256"],
            )

    def test_a_census_that_is_not_there_reads_as_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as where:
            self.assertEqual(against.recorded(Path(where) / "absent.json"), {})


class MainTest(unittest.TestCase):
    def test_with_no_arguments_it_says_how_to_use_it(self) -> None:
        said: list[str] = []

        code = against.main([], say=said.append)

        self.assertEqual((code, "usage" in said[0]), (2, True))

    def test_a_file_that_is_not_there_is_refused(self) -> None:
        said: list[str] = []

        code = against.main(["/nowhere", "/nowhere-either", "/tmp/out.json"], say=said.append)

        self.assertEqual((code, any("no such file" in one for one in said)), (2, True))

    def test_a_sweep_that_confirms_something_writes_its_census(self) -> None:
        said: list[str] = []
        with tempfile.TemporaryDirectory() as where:
            cartridge = Path(where) / "one.sfc"
            cartridge.write_bytes(b"\x00" * 64)
            expanded = Path(where) / "two.sfc"
            expanded.write_bytes(b"..FOUND..")
            out = Path(where) / "census.json"

            code = against.main(
                [str(cartridge), str(expanded), str(out), "0", "4"],
                say=said.append,
                decode=lambda rom, at, n: b"FOUND",
            )

            self.assertEqual((code, out.is_file()), (0, True))

    def test_a_sweep_that_confirms_nothing_says_so(self) -> None:
        said: list[str] = []
        with tempfile.TemporaryDirectory() as where:
            cartridge = Path(where) / "one.sfc"
            cartridge.write_bytes(b"\x00" * 64)
            expanded = Path(where) / "two.sfc"
            expanded.write_bytes(b"nothing here")
            out = Path(where) / "census.json"

            code = against.main(
                [str(cartridge), str(expanded), str(out), "0", "4"],
                say=said.append,
                decode=lambda rom, at, n: b"absent",
            )

        self.assertEqual((code, any("confirmed nothing" in one for one in said)), (1, True))

    def test_with_no_span_named_it_sweeps_the_whole_cartridge(self) -> None:
        said: list[str] = []
        with tempfile.TemporaryDirectory() as where:
            cartridge = Path(where) / "one.sfc"
            cartridge.write_bytes(b"\x00" * 8)
            expanded = Path(where) / "two.sfc"
            expanded.write_bytes(b"FOUND")
            out = Path(where) / "census.json"

            against.main(
                [str(cartridge), str(expanded), str(out)],
                say=said.append,
                decode=lambda rom, at, n: b"FOUND",
            )

            self.assertEqual(json.loads(out.read_text())["swept"], ["0x0", "0x8"])


if __name__ == "__main__":
    unittest.main()
