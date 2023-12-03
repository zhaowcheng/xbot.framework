import unittest
import doctest
import sys
import os
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from xbot import utils


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


class TestUtil(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
