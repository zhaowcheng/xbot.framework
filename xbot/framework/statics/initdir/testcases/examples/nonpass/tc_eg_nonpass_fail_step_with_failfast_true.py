from xbot.framework.utils import assertx

from . import tc_eg_nonpass


class tc_eg_nonpass_fail_step_with_failfast_true(tc_eg_nonpass):
    """
    Testcase failed in any step with FAILFAST set to True.
    """
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare.
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
        Cleanup.
        """
        self.sleep(1)
