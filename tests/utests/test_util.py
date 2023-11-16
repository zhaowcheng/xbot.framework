import unittest
import doctest
import sys
import os
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from xbot import util


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(util))
    return tests


class TestUtil(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
