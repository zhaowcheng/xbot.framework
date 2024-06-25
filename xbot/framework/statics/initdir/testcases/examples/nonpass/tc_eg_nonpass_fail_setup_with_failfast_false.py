from xbot.framework.utils import assertx
from lib.testcase import TestCase

class tc_eg_nonpass_fail_setup_with_failfast_false(TestCase):
    """
    Testcase failed in setup with FAILFAST set to False.
    """
    TIMEOUT = 60
    FAILFAST = False
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare test environment.
        """
        # When the setup fails, regardless of the value of FAILFAST, 
        # subsequent steps will be skipped and immediately execute teardown.
        assertx(1, '==', 0)

    def step1(self):
        """
        Assert 1 == 1.
        """
        assertx(1, '==', 1)

    def step2(self):
        """
        Assert 2 == 2.
        """
        assertx(2, '==', 2)

    def teardown(self):
        """
        Clean up test environment.
        """
        self.sleep(1)
