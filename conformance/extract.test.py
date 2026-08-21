import contextlib
import importlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path
from typing import override

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "conformance"))

extract = importlib.import_module("extract")


def a_rom(streams: Sequence[tuple[int, int]], size: int = 0x2000) -> bytes:
    rom = bytearray(range(256)) * (size // 256)
    for offset, header in streams:
        rom[offset] = header
    return bytes(rom)


class ScanTest(unittest.TestCase):
    def test_a_tagged_stream_is_found(self) -> None:
        rom = bytearray(a_rom([]))
        rom[0x100:0x108] = b"SDD1" + (0x1234).to_bytes(4, "little")

        self.assertEqual(extract.tagged_streams(bytes(rom)), [0x108])

    def test_several_tagged_streams_come_back_in_order(self) -> None:
        rom = bytearray(a_rom([]))
        rom[0x300:0x308] = b"SDD1" + (0x2222).to_bytes(4, "little")
        rom[0x100:0x108] = b"SDD1" + (0x1111).to_bytes(4, "little")

        self.assertEqual(extract.tagged_streams(bytes(rom)), [0x108, 0x308])

    def test_a_rom_with_no_tags_yields_nothing(self) -> None:
        self.assertEqual(extract.tagged_streams(a_rom([])), [])

    def test_a_tag_at_the_very_end_is_not_a_stream(self) -> None:
        rom = bytearray(a_rom([]))
        rom[-8:] = b"SDD1" + (1).to_bytes(4, "little")

        self.assertEqual(extract.tagged_streams(bytes(rom)), [])


class ShapeTest(unittest.TestCase):
    def test_a_header_is_read_at_each_offset(self) -> None:
        rom = a_rom([(0x100, 0x80)])

        found = extract.shapes(rom, [(0x100, 64)])

        self.assertEqual(found["headers"]["128"], 1)

    def test_a_length_is_recorded_with_the_stream(self) -> None:
        found = extract.shapes(a_rom([(0x100, 0x80)]), [(0x100, 64)])

        self.assertEqual(found["lengths"]["64"], 1)

    def test_the_plane_and_context_types_are_split_out(self) -> None:
        found = extract.shapes(a_rom([(0x100, 0xB0)]), [(0x100, 64)])

        self.assertEqual(found["combinations"]["2/3"], 1)

    def test_an_offset_past_the_end_is_skipped(self) -> None:
        found = extract.shapes(a_rom([(0x100, 0x80)]), [(0x100, 64), (0x999999, 64)])

        self.assertEqual(found["streams"], 1)

    def test_several_streams_of_one_shape_are_counted_together(self) -> None:
        rom = a_rom([(0x100, 0x80), (0x200, 0x80)])

        found = extract.shapes(rom, [(0x100, 64), (0x200, 64)])

        self.assertEqual(found["headers"]["128"], 2)

    def test_no_stream_byte_is_carried_into_the_shapes(self) -> None:
        rom = bytearray(a_rom([(0x100, 0x80)]))
        rom[0x101] = 0xDE
        rom[0x102] = 0xAD

        found = extract.shapes(bytes(rom), [(0x100, 64)])

        self.assertNotIn("222", json.dumps(found["headers"]))
        self.assertEqual(
            sorted(found), ["combinations", "comment", "headers", "lengths", "streams"]
        )


class TableTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.root = tempfile.mkdtemp(prefix="extract-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_a_table_of_pairs_reads_back(self) -> None:
        path = Path(self.root) / "t.json"
        path.write_text(json.dumps([[256, 64], [512, 128]]))

        self.assertEqual(extract.table(path), [(256, 64), (512, 128)])

    def test_a_table_may_name_its_streams(self) -> None:
        path = Path(self.root) / "t.json"
        path.write_text(json.dumps({"streams": [[256, 64]]}))

        self.assertEqual(extract.table(path), [(256, 64)])


class MainTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.root = tempfile.mkdtemp(prefix="extract-main-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.rom = Path(self.root) / "rom.sfc"
        blob = bytearray(a_rom([(0x108, 0x80)]))
        blob[0x100:0x108] = b"SDD1" + (0x1234).to_bytes(4, "little")
        self.rom.write_bytes(bytes(blob))

    def run_main(self, argv: list[str]) -> tuple[int, str]:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = extract.main(argv)
        return code, captured.getvalue()

    def test_no_arguments_explains_how_to_call_it(self) -> None:
        code, output = self.run_main([])

        self.assertEqual(code, 2)
        self.assertIn("usage", output)

    def test_a_rom_that_is_not_there_is_reported(self) -> None:
        code, output = self.run_main([str(Path(self.root) / "absent.sfc"), "out.json"])

        self.assertEqual(code, 2)
        self.assertIn("no rom at", output)

    def test_a_tagged_rom_is_turned_into_a_shape_profile(self) -> None:
        out = Path(self.root) / "shapes.json"

        code, output = self.run_main([str(self.rom), str(out)])

        self.assertEqual(code, 0)
        self.assertIn("1 streams", output)
        self.assertEqual(json.loads(out.read_text())["streams"], 1)

    def test_a_rom_with_no_streams_says_so(self) -> None:
        plain = Path(self.root) / "plain.sfc"
        plain.write_bytes(a_rom([]))

        code, output = self.run_main([str(plain), str(Path(self.root) / "s.json")])

        self.assertEqual(code, 1)
        self.assertIn("no streams", output)

    def test_a_table_can_be_given_instead_of_scanning(self) -> None:
        table = Path(self.root) / "t.json"
        table.write_text(json.dumps([[0x108, 64]]))
        out = Path(self.root) / "shapes.json"

        code, _ = self.run_main([str(self.rom), str(out), str(table)])

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.read_text())["streams"], 1)


if __name__ == "__main__":
    unittest.main()
