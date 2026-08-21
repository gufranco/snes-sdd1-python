import contextlib
import hashlib
import importlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import override

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "conformance"))

vectors = importlib.import_module("vectors")


class DefinitionTest(unittest.TestCase):
    def test_the_repository_ships_a_vector_set(self) -> None:
        self.assertTrue(vectors.load()["cases"])

    def test_the_input_matches_the_digest_recorded_beside_it(self) -> None:
        found = vectors.load()

        self.assertEqual(
            hashlib.sha256(bytes.fromhex(found["input"])).hexdigest(),
            found["input_sha256"],
        )

    def test_the_set_names_the_decoder_it_came_from(self) -> None:
        self.assertIn("snes9x", vectors.load()["reference"])

    def test_a_vector_file_is_read_from_where_it_is_asked_for(self) -> None:
        with tempfile.TemporaryDirectory() as where:
            path = Path(where) / "v.json"
            path.write_text(json.dumps({"cases": [], "input": "", "reference": "x"}))

            self.assertEqual(vectors.load(path)["reference"], "x")


class CoverageTest(unittest.TestCase):
    def test_the_set_reaches_every_combination_of_plane_and_context_type(self) -> None:
        found = vectors.load()
        blob = bytes.fromhex(found["input"])

        seen = {
            (blob[case["offset"]] >> 6, (blob[case["offset"]] >> 4) & 3) for case in found["cases"]
        }

        self.assertEqual(len(seen), 16)

    def test_the_set_reaches_more_than_one_output_length(self) -> None:
        lengths = {case["length"] for case in vectors.load()["cases"]}

        self.assertGreater(len(lengths), 5)


class CheckTest(unittest.TestCase):
    def test_a_matching_case_reports_nothing(self) -> None:
        found = vectors.load()
        blob = bytes.fromhex(found["input"])

        self.assertIsNone(vectors.check(blob, found["cases"][0]))

    def test_a_disagreement_names_the_offset_and_length(self) -> None:
        found = vectors.load()
        blob = bytes.fromhex(found["input"])
        wrong = dict(found["cases"][0], output_sha256="0" * 64)

        reported = vectors.check(blob, wrong)

        self.assertIn(str(wrong["offset"]), reported)

    def test_a_case_that_cannot_decode_is_reported_rather_than_raising(self) -> None:
        wrong = {"offset": 10_000_000, "length": 16, "output_sha256": "0" * 64}

        self.assertIsNotNone(vectors.check(b"\x00\x00", wrong))


class RunTest(unittest.TestCase):
    def test_the_whole_shipped_set_agrees(self) -> None:
        found = vectors.load()

        passed, failed, examples = vectors.run(found)

        self.assertEqual(failed, 0)
        self.assertEqual(examples, [])
        self.assertEqual(passed, len(found["cases"]))

    def test_a_disagreeing_case_is_counted_and_kept(self) -> None:
        found = vectors.load()
        broken = dict(found, cases=[dict(found["cases"][0], output_sha256="0" * 64)])

        passed, failed, examples = vectors.run(broken)

        self.assertEqual((passed, failed), (0, 1))
        self.assertEqual(len(examples), 1)

    def test_only_a_few_examples_are_kept(self) -> None:
        found = vectors.load()
        broken = dict(
            found,
            cases=[dict(case, output_sha256="0" * 64) for case in found["cases"][:50]],
        )

        _, _, examples = vectors.run(broken)

        self.assertLessEqual(len(examples), vectors.EXAMPLE_LIMIT)


class MainTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.root = tempfile.mkdtemp(prefix="vectors-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def run_main(self, argv: list[str]) -> tuple[int, str]:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = vectors.main(argv)
        return code, captured.getvalue()

    def test_no_arguments_runs_the_set_that_ships(self) -> None:
        code, output = self.run_main([])

        self.assertEqual(code, 0)
        self.assertIn("agreed", output)

    def test_a_set_that_is_not_there_is_reported(self) -> None:
        code, output = self.run_main([str(Path(self.root) / "absent.json")])

        self.assertEqual(code, 2)
        self.assertIn("no vectors at", output)

    def test_a_disagreeing_set_fails_and_names_the_case(self) -> None:
        found = vectors.load()
        broken = dict(found, cases=[dict(found["cases"][0], output_sha256="0" * 64)])
        path = Path(self.root) / "broken.json"
        path.write_text(json.dumps(broken))

        code, output = self.run_main([str(path)])

        self.assertEqual(code, 1)
        self.assertIn("1 did not", output)


if __name__ == "__main__":
    unittest.main()
