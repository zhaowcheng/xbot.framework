from xbot.framework.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_timeout(TestCase):
    """
    Testcase execution timeout.
    """
    TIMEOUT = 2
    FAILFAST = True
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare test environment.
        """
        self.info('Starting setup')

    def step1(self):
        """
        Test step 1.
        """
        # This will be forced to end due to timeout, subsequent 
        # steps will be skipped and immediately execute teardown.
        self.sleep(3)

    def step2(self):
        """
        Test step 2.
        """
        self.info('Starting test step 2')

    def teardown(self):
        """
        Clean up test environment.
        """
        self.info('Starting teardown')
