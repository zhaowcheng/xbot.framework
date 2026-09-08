from xbot.framework.utils import assertx

from . import tc_eg_nonpass


class tc_eg_nonpass_skip_not_included(tc_eg_nonpass):
    """
    Testcase skipped due to not containing tag matching the `testset.tags.include`.
    """
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
