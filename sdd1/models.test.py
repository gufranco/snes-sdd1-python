import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sdd1
from sdd1 import errors, models


class CatalogueTest(unittest.TestCase):
    def test_the_package_names_every_model_it_covers(self) -> None:
        self.assertIn("sdd1", models.MODELS)

    def test_a_model_says_what_it_is_and_what_it_interleaves(self) -> None:
        found = models.lookup("sdd1")

        self.assertTrue(found.summary)
        self.assertEqual(found.planes, 8)
        self.assertEqual(found.contexts, 32)

    def test_a_model_name_is_matched_however_it_is_written(self) -> None:
        for written in ("SDD1", "s-dd1", "S_DD_1", "sdd"):
            self.assertEqual(models.lookup(written).name, "sdd1")

    def test_a_model_the_package_does_not_have_is_refused_by_name(self) -> None:
        with self.assertRaises(errors.UnknownModelError):
            models.lookup("spc7110")

    def test_the_refusal_lists_what_is_available(self) -> None:
        with self.assertRaises(errors.UnknownModelError) as raised:
            models.lookup("nonsense")

        self.assertIn("sdd1", str(raised.exception))

    def test_a_model_prints_as_its_name_and_planes(self) -> None:
        printed = repr(models.lookup("sdd1"))

        self.assertIn("sdd1", printed)
        self.assertIn("8", printed)


class BuildTest(unittest.TestCase):
    def test_a_chip_is_built_from_its_model_name(self) -> None:
        self.assertEqual(sdd1.Chip(model="sdd1").model, "sdd1")

    def test_the_default_model_is_the_one_the_cartridges_carry(self) -> None:
        self.assertEqual(sdd1.Chip("sdd1").model, "sdd1")

    def test_a_built_chip_decompresses_the_same_way_the_function_does(self) -> None:
        blob = bytes(range(256)) * 8

        self.assertEqual(
            sdd1.Chip("sdd1").decompress(blob, 0, 32).data,
            sdd1.decompress(blob, 0, 32).data,
        )

    def test_a_model_the_package_does_not_have_is_refused_at_construction(self) -> None:
        with self.assertRaises(errors.UnknownModelError):
            sdd1.Chip(model="cx4")


class NamingNoneTest(unittest.TestCase):
    """That leaving the model out is refused, and refused usefully."""

    def test_building_without_naming_a_model_is_refused(self) -> None:
        with self.assertRaises(errors.UnknownModelError):
            sdd1.Chip()

    def test_and_the_refusal_names_every_model_there_is(self) -> None:
        with self.assertRaises(errors.UnknownModelError) as caught:
            sdd1.Chip()

        missing = [name for name in sdd1.MODELS if name not in str(caught.exception)]

        self.assertEqual(missing, [])

    def test_nothing_named_describe_is_published(self) -> None:
        self.assertFalse(hasattr(sdd1, "describe"))

    def test_and_no_default_model_is_published_either(self) -> None:
        self.assertFalse(hasattr(sdd1, "DEFAULT_MODEL"))


if __name__ == "__main__":
    unittest.main()
