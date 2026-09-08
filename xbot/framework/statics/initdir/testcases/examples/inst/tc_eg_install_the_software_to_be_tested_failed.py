from . import tc_eg_inst


class tc_eg_install_the_software_to_be_tested_failed(tc_eg_inst):
    """
    Install the software to be tested failed.
    """
    def setup(self):
        """
        Prepare test environment.
        """
        pass

    def step1(self):
        """
        Installation.
        """
        raise Exception('Installation of the software to be tested failed.')

    def teardown(self):
        """
        Clean up test environment.
        """
        pass
