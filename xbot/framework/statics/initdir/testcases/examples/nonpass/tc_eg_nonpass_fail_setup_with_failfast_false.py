from xbot.framework.utils import assertx

from . import tc_eg_nonpass


class tc_eg_nonpass_fail_setup_with_failfast_false(tc_eg_nonpass):
    """
    Testcase failed in setup with FAILFAST set to False.
    """
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
