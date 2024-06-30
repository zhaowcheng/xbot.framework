from xbot.framework import testcase

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
        return self.__testbed
