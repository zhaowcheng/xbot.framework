from xbot.framework.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_skip_not_included(TestCase):
    """
    Testcase skipped due to not containing tag matching the `testset.tags.include`.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = []

    def setup(self):
        """
        Prepare test environment.
        """
        self.info('Starting setup')

    def step1(self):
        """
        Test step 1.
        """
        self.info('Starting test step 1')

    def teardown(self):
        """
        Clean up test environment.
        """
        self.info('Starting teardown')
