from lib.testcase import TestCase


# The class name will be treated as the testcase id, 
# and should be consistent with the file name.
class testcase_template(TestCase):
    """
    Testcase short description.

    @TestcaseName: xxx

    @PresetSteps:
        1.xxxx
        2.xxxx
        3.xxxx

    @TestSteps:
        1.xxxx
        2.xxxx
        3.xxxx
        
    @ExpectedResults:
        1.xxxx
        2.xxxx
        3.xxxx
    """

    # Max execution time(minutes).
    TIMEOUT = 5
    # Testcase tags.
    TAGS = []

    def setup(self):
        """
        Preset steps.
        """
        pass

    def process(self):
        """
        Test steps.
        """
        pass

    def teardown(self):
        """
        Post steps.
        """
        pass
