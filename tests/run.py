"""
Entry point for running all tests in the tests directory.
"""

import unittest

from pathlib import Path


if __name__ == '__main__':
    startdir = Path(__file__).parent
    testsuit = unittest.TestLoader().discover(startdir)
    result = unittest.TextTestRunner(verbosity=2).run(testsuit)
    raise SystemExit(0 if result.wasSuccessful() else 1)
