from . import tc_eg_inst


class tc_eg_install_the_software_to_be_tested_successful(tc_eg_inst):
    """
    Install the software to be tested successful.
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
        self.info('The software was successfully installed.')

    def teardown(self):
        """
        Clean up test environment.
        """
        pass
