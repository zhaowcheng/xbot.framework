from lib.testcase import TestCase


class tc_eg_install_the_software_to_be_tested_successful(TestCase):
    """
    Install the software to be tested successful.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = []

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
