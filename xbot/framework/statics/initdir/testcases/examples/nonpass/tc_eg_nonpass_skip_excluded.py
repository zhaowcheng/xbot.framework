from xbot.framework.utils import assertx
from lib.testcase import TestCase

class tc_eg_nonpass_skip_excluded(TestCase):
    """
    Testcase skipped due to containing tag(s) matching the `testset.tags.exclude`.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1', 'tag2']

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
