from xbot.framework import testcase

from typing import cast

from .testbed import TestBed


class TestCase(testcase.TestCase):
    """
    Implement as needed.
    """
    @property
    def testbed(self) -> TestBed:
        """
        TestBed instance.
        """
        return cast(TestBed, super().testbed)
