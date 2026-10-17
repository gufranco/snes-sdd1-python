import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sdd1


class CatalogueTest(unittest.TestCase):
    def test_the_package_names_every_model_it_covers(self) -> None:
        # Arrange
        catalogue = sdd1.MODELS

        # Act
        names = sorted(catalogue)

        # Assert
        self.assertEqual(names, ["sdd1"])

    def test_a_model_says_what_it_is_and_what_it_interleaves(self) -> None:
        # Arrange
        catalogue = sdd1.MODELS

        # Act
        found = catalogue["sdd1"]

        # Assert
        self.assertIn("decompressor", found.summary)
        self.assertEqual((found.name, found.planes, found.contexts), ("sdd1", 8, 32))

    def test_a_model_name_is_matched_however_it_is_written(self) -> None:
        # Arrange
        written = ("SDD1", "s-dd1", "S_DD_1", "sdd", "nintendosdd1")

        # Act
        found = [sdd1.Chip(name).model for name in written]

        # Assert
        self.assertEqual(found, ["sdd1"] * len(written))

    def test_a_model_the_package_does_not_have_is_refused_by_name(self) -> None:
        # Arrange
        def attempt() -> Any:
            return sdd1.Chip("spc7110")

        # Act
        with self.assertRaises(sdd1.UnknownModelError) as raised:
            attempt()

        # Assert
        self.assertIn("spc7110 is not a model this package covers", str(raised.exception))

    def test_the_refusal_lists_what_is_available(self) -> None:
        # Arrange
        def attempt() -> Any:
            return sdd1.Chip("nonsense")

        # Act
        with self.assertRaises(sdd1.UnknownModelError) as raised:
            attempt()

        # Assert
        self.assertIn("it has sdd1", str(raised.exception))

    def test_a_model_prints_as_its_name_and_planes(self) -> None:
        # Arrange
        model = sdd1.MODELS["sdd1"]

        # Act
        printed = repr(model)

        # Assert
        self.assertEqual(printed, "<Model sdd1, up to 8 bit planes>")


class BuildTest(unittest.TestCase):
    def test_a_chip_is_built_from_its_model_name(self) -> None:
        # Arrange
        name = "sdd1"

        # Act
        chip = sdd1.Chip(model=name)

        # Assert
        self.assertEqual(chip.model, "sdd1")

    def test_the_default_model_is_the_one_the_cartridges_carry(self) -> None:
        # Arrange
        name = "sdd1"

        # Act
        chip = sdd1.Chip(name)

        # Assert
        self.assertEqual(chip.model, "sdd1")

    def test_a_reset_hands_the_part_back(self) -> None:
        # Arrange
        chip = sdd1.Chip("sdd1")

        # Act
        handed = chip.reset()

        # Assert
        self.assertIs(handed, chip)

    def test_a_built_chip_decompresses_the_same_way_the_function_does(self) -> None:
        # Arrange
        blob = bytes(range(256)) * 8

        # Act
        found = sdd1.Chip("sdd1").decompress(blob, 0, 32)

        # Assert
        self.assertEqual(found, sdd1.decompress(blob, 0, 32))

    def test_a_model_the_package_does_not_have_is_refused_at_construction(self) -> None:
        # Arrange
        def attempt() -> Any:
            return sdd1.Chip(model="cx4")

        # Act
        with self.assertRaises(sdd1.UnknownModelError) as raised:
            attempt()

        # Assert
        self.assertIn("cx4", str(raised.exception))


class NamingNoneTest(unittest.TestCase):
    def test_building_without_naming_a_model_is_refused(self) -> None:
        # Arrange
        def attempt() -> Any:
            return sdd1.Chip()

        # Act
        with self.assertRaises(sdd1.UnknownModelError) as raised:
            attempt()

        # Assert
        self.assertIn("will not choose one for you", str(raised.exception))

    def test_and_the_refusal_names_every_model_there_is(self) -> None:
        # Arrange
        def attempt() -> Any:
            return sdd1.Chip()

        # Act
        with self.assertRaises(sdd1.UnknownModelError) as caught:
            attempt()

        # Assert
        self.assertEqual([name for name in sdd1.MODELS if name not in str(caught.exception)], [])

    def test_nothing_named_describe_is_published(self) -> None:
        # Arrange
        package = sdd1

        # Act
        found = hasattr(package, "describe")

        # Assert
        self.assertFalse(found)

    def test_and_no_default_model_is_published_either(self) -> None:
        # Arrange
        package = sdd1

        # Act
        found = hasattr(package, "DEFAULT_MODEL")

        # Assert
        self.assertFalse(found)


if __name__ == "__main__":
    unittest.main()
