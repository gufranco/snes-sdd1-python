import contextlib
import importlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "conformance"))

corpus = importlib.import_module("corpus")


class DefinitionTest(unittest.TestCase):
    def test_the_repository_ships_a_corpus(self):
        self.assertTrue(corpus.load()["cases"])

    def test_the_corpus_names_the_decoder_its_answers_came_from(self):
        self.assertIn("snes9x", corpus.load()["reference"])

    def test_the_corpus_records_the_census_it_was_shaped_by(self):
        found = corpus.load()["census"]

        self.assertGreater(found["streams"], 0)
        self.assertTrue(found["combinations"])

    def test_a_corpus_is_read_from_where_it_is_asked_for(self):
        with tempfile.TemporaryDirectory() as where:
            path = Path(where) / "c.json"
            path.write_text(json.dumps({"cases": [], "reference": "x", "body_seed": 1}))

            self.assertEqual(corpus.load(path)["reference"], "x")


class BodyTest(unittest.TestCase):
    def test_the_image_is_rebuilt_from_its_seed(self):
        found = corpus.load()

        self.assertEqual(len(corpus.body(found)), found["body_bytes"])

    def test_the_same_seed_rebuilds_the_same_image(self):
        found = corpus.load()

        self.assertEqual(corpus.body(found), corpus.body(found))

    def test_every_case_has_its_real_header_at_its_offset(self):
        found = corpus.load()
        image = corpus.body(found)

        wrong = [c for c in found["cases"] if image[c["offset"]] != c["header"]]

        self.assertEqual(wrong, [])


class ShapeTest(unittest.TestCase):
    def test_every_header_the_cartridges_use_appears(self):
        found = corpus.load()

        self.assertGreater(len({case["header"] for case in found["cases"]}), 60)

    def test_the_cases_reach_a_whole_block(self):
        found = corpus.load()

        self.assertIn(0x10000, {case["length"] for case in found["cases"]})

    def test_the_cases_reach_short_streams_as_well(self):
        found = corpus.load()

        self.assertLess(min(case["length"] for case in found["cases"]), 16)

    def test_the_corpus_holds_no_compressed_byte_of_a_cartridge(self):
        found = corpus.load()

        self.assertEqual(
            sorted(found["cases"][0]),
            ["header", "length", "offset", "output_head", "output_sha256"],
        )


class CheckTest(unittest.TestCase):
    def test_a_matching_case_reports_nothing(self):
        found = corpus.load()

        self.assertIsNone(corpus.check(corpus.body(found), found["cases"][0]))

    def test_the_image_is_shared_by_every_case(self):
        found = corpus.load()

        self.assertGreater(len(found["cases"]), 1)

    def test_a_disagreement_names_the_header_and_length(self):
        found = corpus.load()
        wrong = dict(found["cases"][0], output_sha256="0" * 64)

        reported = corpus.check(corpus.body(found), wrong)

        self.assertIn(str(wrong["length"]), reported)

    def test_a_case_that_cannot_decode_is_reported_rather_than_raising(self):
        wrong = {"header": 0, "offset": 10_000_000, "length": 16, "output_sha256": "0" * 64}

        self.assertIsNotNone(corpus.check(b"\x00\x00", wrong))


class RunTest(unittest.TestCase):
    def test_the_whole_shipped_corpus_agrees(self):
        found = corpus.load()

        passed, failed, examples = corpus.run(found)

        self.assertEqual(failed, 0)
        self.assertEqual(examples, [])
        self.assertEqual(passed, len(found["cases"]))

    def test_a_disagreeing_case_is_counted_and_kept(self):
        found = corpus.load()
        broken = dict(found, cases=[dict(found["cases"][0], output_sha256="0" * 64)])

        passed, failed, examples = corpus.run(broken)

        self.assertEqual((passed, failed), (0, 1))
        self.assertEqual(len(examples), 1)

    def test_only_a_few_examples_are_kept(self):
        found = corpus.load()
        broken = dict(
            found, cases=[dict(case, output_sha256="0" * 64) for case in found["cases"][:50]]
        )

        _, _, examples = corpus.run(broken)

        self.assertLessEqual(len(examples), corpus.EXAMPLE_LIMIT)


class MainTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="corpus-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def run_main(self, argv):
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = corpus.main(argv)
        return code, captured.getvalue()

    def test_no_arguments_runs_the_corpus_that_ships(self):
        code, output = self.run_main([])

        self.assertEqual(code, 0)
        self.assertIn("agreed", output)

    def test_a_corpus_that_is_not_there_is_reported(self):
        code, output = self.run_main([str(Path(self.root) / "absent.json")])

        self.assertEqual(code, 2)
        self.assertIn("no corpus at", output)

    def test_a_disagreeing_corpus_fails_and_names_the_case(self):
        found = corpus.load()
        broken = dict(found, cases=[dict(found["cases"][0], output_sha256="0" * 64)])
        path = Path(self.root) / "broken.json"
        path.write_text(json.dumps(broken))

        code, output = self.run_main([str(path)])

        self.assertEqual(code, 1)
        self.assertIn("1 did not", output)


if __name__ == "__main__":
    unittest.main()
