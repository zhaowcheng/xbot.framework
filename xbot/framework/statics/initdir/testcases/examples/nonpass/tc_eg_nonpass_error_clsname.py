from xbot.framework.utils import assertx

from . import tc_eg_nonpass


class tc_eg_nonpass_class_name_incorrect(tc_eg_nonpass):
    """
    Testcase with incorrect class name (not consistent with the filename).
    """
    FAILFAST = False
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare.
        """
        self.info('Starting setup')

    def step1(self):
        """
        Test step 1.
        """
        self.info('Starting test step 1')

    def teardown(self):
        """
        Cleanup.
        """
        self.info('Starting teardown')