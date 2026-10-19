import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conformance import traced

NOISE = random.Random(1996).randbytes(4096)


def an_image(starts: dict[int, bytes]) -> bytes:
    body = bytearray(random.Random(20261019).randbytes(0x8000))
    for at, stream in starts.items():
        body[at : at + len(stream)] = stream
    return bytes(body)


def a_tagged_build(starts: list[int], lengths: list[int]) -> bytes:
    body = bytearray(0x8000)
    destination = 0x10000
    for at, length in zip(starts, [*lengths, 0], strict=True):
        body[at : at + 8] = b"SDD1" + destination.to_bytes(4, "little")
        destination += length
    return bytes(body)


SHARED = bytes([0x80]) + NOISE[1:256]

OWN = bytes([0x10]) + NOISE[256:512]


class TableTest(unittest.TestCase):
    def test_a_table_written_as_json_is_read_as_offset_and_length_pairs(self) -> None:
        # Arrange
        folder = Path(tempfile.mkdtemp())
        (folder / "table.json").write_text(json.dumps([[16, 32], ["0x40", 8]]))

        # Act
        found = traced.table(folder / "table.json")

        # Assert
        self.assertEqual(found, [(16, 32), (64, 8)])

    def test_a_table_written_as_a_python_tuple_is_read_without_running_it(self) -> None:
        # Arrange
        folder = Path(tempfile.mkdtemp())
        (folder / "table.py").write_text(
            "import os\nos.remove('nothing')\nSTREAMS = (\n    (0x10, 32),\n    (0x40, 8),\n)\n"
        )

        # Act
        found = traced.table(folder / "table.py")

        # Assert
        self.assertEqual(found, [(16, 32), (64, 8)])

    def test_a_python_file_without_a_table_gives_none(self) -> None:
        # Arrange
        folder = Path(tempfile.mkdtemp())
        (folder / "table.py").write_text("OTHER = ((1, 2),)\n")

        # Act
        found = traced.table(folder / "table.py")

        # Assert
        self.assertEqual(found, [])


class AgreementTest(unittest.TestCase):
    def test_a_stream_expanding_to_the_same_bytes_as_one_in_the_other_build_is_counted(
        self,
    ) -> None:
        # Arrange
        traced_image = an_image({0x100: SHARED, 0x400: OWN})
        indexed_image = an_image({0x2000: SHARED})

        # Act
        found = traced.agreement(
            traced_image, [(0x100, 64), (0x400, 64)], indexed_image, [(0x2000, 64)]
        )

        # Assert
        self.assertEqual(found, {"identical": 1, "control": 0, "streams": 2})

    def test_the_control_moves_every_start_one_byte_on(self) -> None:
        # Arrange
        traced_image = an_image({0x100: bytes([0x80]) + SHARED})
        indexed_image = an_image({0x2000: SHARED})

        # Act
        found = traced.agreement(traced_image, [(0x100, 64)], indexed_image, [(0x2000, 64)])

        # Assert
        self.assertEqual(found, {"identical": 0, "control": 1, "streams": 1})


class MainTest(unittest.TestCase):
    def arranged(self) -> tuple[Path, list[str]]:
        folder = Path(tempfile.mkdtemp())
        (folder / "traced.sfc").write_bytes(an_image({0x100: SHARED, 0x400: OWN}))
        (folder / "indexed.sfc").write_bytes(an_image({0x2000: SHARED}))
        (folder / "index.sfc").write_bytes(a_tagged_build([0x2000, 0x3000], [64]))
        (folder / "table.json").write_text(json.dumps([[0x100, 64], [0x400, 64]]))
        names = ("traced.sfc", "table.json", "indexed.sfc", "index.sfc", "out.json")
        return folder, [str(folder / name) for name in names]

    def test_a_run_writes_the_census_and_the_agreement(self) -> None:
        # Arrange
        folder, argv = self.arranged()

        # Act
        status = traced.main(argv, say=lambda line: None)

        # Assert
        written = json.loads((folder / "out.json").read_text())
        self.assertEqual(status, 0)
        self.assertEqual(
            (written["streams"], written["agreement"], len(written["measuredFrom"])),
            (2, {"identical": 1, "control": 0, "streams": 2}, 3),
        )

    def test_and_says_what_it_found(self) -> None:
        # Arrange
        _folder, argv = self.arranged()
        said: list[str] = []

        # Act
        traced.main(argv, say=said.append)

        # Assert
        self.assertEqual(
            said[0], "  2 traced streams, 1 identical to an indexed stream, 0 in the control"
        )

    def test_too_few_arguments_is_a_usage_error(self) -> None:
        # Arrange
        said: list[str] = []

        # Act
        status = traced.main(["one"], say=said.append)

        # Assert
        self.assertEqual((status, said[0][:6]), (2, "usage:"))

    def test_a_missing_file_is_refused(self) -> None:
        # Arrange
        folder, argv = self.arranged()
        (folder / "index.sfc").unlink()
        said: list[str] = []

        # Act
        status = traced.main(argv, say=said.append)

        # Assert
        self.assertEqual((status, said[0]), (2, f"  no such file: {folder / 'index.sfc'}"))

    def test_an_empty_table_is_refused(self) -> None:
        # Arrange
        folder, argv = self.arranged()
        (folder / "table.json").write_text("[]")
        said: list[str] = []

        # Act
        status = traced.main(argv, say=said.append)

        # Assert
        self.assertEqual((status, said[0]), (1, "  the table names no stream"))


class RecordTest(unittest.TestCase):
    def test_the_shipped_record_separates_from_its_control(self) -> None:
        # Arrange
        held = traced.recorded()

        # Act
        agreement = held["agreement"]

        # Assert
        self.assertEqual(
            (agreement["streams"], agreement["identical"], agreement["control"]),
            (2855, 2732, 0),
        )

    def test_and_its_census_counts_every_stream_in_the_table(self) -> None:
        # Arrange
        held = traced.recorded()

        # Act
        counted = sum(held["headers"].values())

        # Assert
        self.assertEqual((counted, held["streams"]), (2855, 2855))


if __name__ == "__main__":
    unittest.main()
