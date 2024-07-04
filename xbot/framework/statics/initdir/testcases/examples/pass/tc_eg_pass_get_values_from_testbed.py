from xbot.framework.utils import assertx
from lib.testcase import TestCase


class tc_eg_pass_get_values_from_testbed(TestCase):
    """
    Get information from the testbed and perform checks.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare test environment.
        """
        pass

    def step1(self):
        """
        Expect the value of `example.key1` to be `value1`.
        """
        value1 = self.testbed.get('example.key1')
        assertx(value1, '==', 'value1')

    def step2(self):
        """
        Expect the value of `example.key2."key2-1"` to be `value2-1`.
        """
        value2 = self.testbed.get('example.key2."key2-1"')
        assertx(value2, '==', 'value2-1')

    def step3(self):
        """
        Expect the value of `example.key3[1]` to be `value3-2`.
        """
        value3 = self.testbed.get('example.key3[1]')
        assertx(value3, '==', 'value3-2')

    def step4(self):
        """
        Expect the value of `example.key4[?name=='jack']` to be `[{'name': 'jack', 'age', '20'}]`.
        """
        value4 = self.testbed.get("example.key4[?name=='jack']")
        assertx(value4, '==', [{'name': 'jack', 'age': 20}])

    def step5(self):
        """
        Expect the value of `example.key4[?name=='lily']` to be `[]`.
        """
        value5 = self.testbed.get("example.key5[?name=='lily']")
        assertx(value5, '==', None)

    def teardown(self):
        """
        Clean up test environment.
        """
        self.sleep(1)
