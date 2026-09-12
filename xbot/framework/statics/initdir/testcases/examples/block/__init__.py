from .. import tc_eg


class tc_eg_block(tc_eg):
    """
    Base of `testcases/examples/block` directory.
    """
    def setup(self):
        """
        Prepare.
        """
        raise Exception('Super class setup failed.')

    def teardown(self):
        """
        Cleanup.
        """
        pass
