import unittest

from alphapulldown_dnaaf_screen import __version__


class PackageImportTests(unittest.TestCase):
    def test_package_imports(self) -> None:
        self.assertEqual(__version__, "0.0.0")


if __name__ == "__main__":
    unittest.main()
