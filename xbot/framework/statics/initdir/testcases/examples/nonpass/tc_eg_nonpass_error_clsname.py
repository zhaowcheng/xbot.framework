from xbot.framework.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_class_name_incorrect(TestCase):
    """
    Testcase with incorrect class name (not consistent with the filename).
    """
    TIMEOUT = 60
    FAILFAST = False
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
        self.info('Starting test step 1')

    def teardown(self):
        """
        Clean up test environment.
        """
        self.info('Starting teardown')