from xbot.framework.utils import assertx

from . import tc_eg_block


class tc_eg_block_parent_setup_not_pass(tc_eg_block):
    """
    Blocked due to parent class's setup is not passed.
    """
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare.
        """
        pass

    def step1(self):
        """
        Step 1.
        """
        self.info('Step 1.')

    def teardown(self):
        """
        Cleanup.
        """
        pass
