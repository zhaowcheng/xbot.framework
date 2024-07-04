"""
Entry point for running all tests in the tests directory.
"""

import unittest

from pathlib import Path


if __name__ == '__main__':
    startdir = Path(__file__).parent
    testsuit = unittest.TestLoader().discover(startdir)
    unittest.TextTestRunner(verbosity=2).run(testsuit)
