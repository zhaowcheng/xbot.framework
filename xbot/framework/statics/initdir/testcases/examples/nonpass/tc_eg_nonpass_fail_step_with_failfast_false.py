from xbot.framework.utils import assertx
from lib.testcase import TestCase

class tc_eg_nonpass_fail_step_with_failfast_false(TestCase):
    """
    Testcase failed in any step with FAILFAST set to False.
    """
    TIMEOUT = 60
    FAILFAST = False
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare test environment.
        """
        pass

    def step1(self):
        """
        Assert 1 == 2.
        """
        # This will fail, but since FAILFAST is set to False, 
        # it will continue executing subsequent test steps.
        assertx(1, '==', 2)

    def step2(self):
        """
        Assert 1 == 1.
        """
        assertx(1, '==', 1)

    def teardown(self):
        """
        Clean up test environment.
        """
        self.sleep(1)
