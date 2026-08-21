from lib.testcase import TestCase


class tc_eg_install_the_software_to_be_tested_failed(TestCase):
    """
    Install the software to be tested failed.
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
        raise Exception('Installation of the software to be tested failed.')

    def teardown(self):
        """
        Clean up test environment.
        """
        pass
