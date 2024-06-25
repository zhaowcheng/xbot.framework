from xbot.framework.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_error_syntax(TestCase):
    """
    Testcase with syntax error.
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
        # noinspection PyUnreachableCode
        self.info('Starting test step 1'  # type: ignore

    def teardown(self):
        """
        Clean up test environment.
        """
        self.info('Starting teardown')
