from xbot.framework.utils import assertx

from . import tc_eg_nonpass


class tc_eg_nonpass_error_syntax(tc_eg_nonpass):
    """
    Testcase with syntax error.
    """
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
