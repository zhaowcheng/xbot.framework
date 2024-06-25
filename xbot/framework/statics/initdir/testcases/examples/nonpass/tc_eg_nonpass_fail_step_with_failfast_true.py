from xbot.framework.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_fail_step_with_failfast_true(TestCase):
    """
    Testcase failed in any step with FAILFAST set to True.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare test environment.
        """
        pass

    def step1(self):
        """
        Assert 1 == 2
        """
        # This will fail, and due to FAILFAST=True, it will skip the 
        # subsequent test steps and immediately execute teardown.
        assertx(1, '==', 2)

    def step2(self):
        """
        Assert 1 == 1
        """
        assertx(1, '==', 1)

    def teardown(self):
        """
        Clean up test environment.
        """
        self.sleep(1)
