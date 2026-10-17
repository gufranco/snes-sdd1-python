import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sdd1  # noqa: E402

WRITTEN = re.compile(r"""^VERSION = "([^"]+)"$""", re.MULTILINE)


class VersionTest(unittest.TestCase):
    def test_the_version_is_three_numbers(self) -> None:
        # Arrange
        version = sdd1.__version__

        # Act
        parts = version.split(".")

        # Assert
        self.assertEqual([part.isdigit() for part in parts], [True, True, True])

    def test_the_package_reports_the_version_the_release_job_writes(self) -> None:
        # Arrange
        written = WRITTEN.findall((ROOT / "sdd1" / "version.py").read_text())

        # Act
        reported = sdd1.__version__

        # Assert
        self.assertEqual(written, [reported])


if __name__ == "__main__":
    unittest.main()
