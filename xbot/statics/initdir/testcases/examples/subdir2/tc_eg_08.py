from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_08(TestCase):
    """
    FAILFAST 属性为 False 的用例。
    """
    TIMEOUT = 60
    FAILFAST = False
    TAGS = ['tag1']

    def setup(self):
        """
        无
        """
        pass

    def step1(self):
        """
        获取 `example.key1` 的值并检查，值应为 `value1`。
        """
        value1 = self.testbed.get('example.key1')
        assertx(value1, '==', 'value1')

    def step2(self):
        """
        获取 `example.key2.key2-1` 的值并检查，值应为 `value2-2`。
        """
        value2 = self.testbed.get('example.key2.key2-1')
        assertx(value2, '==', 'value2-2')

    def step3(self):
        """
        获取 `example.key3[1]` 的值并检查，值应为 `value3-2`。
        """
        value3 = self.testbed.get('example.key3[1]')
        assertx(value3, '==', 'value3-2')

    def teardown(self):
        """
        睡 1 秒模拟清理步骤。
        """
        self.sleep(1)
