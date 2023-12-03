from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_03(TestCase):
    """
    失败的测试用例。
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1']

    def setup(self):
        """
        无
        """
        pass

    def step1(self):
        """
        断言 1 == 2。
        """
        assertx(1, '==', 2)

    def step2(self):
        """
        断言 1 == 1。
        """
        assertx(1, '==', 1)

    def teardown(self):
        """
        睡 1 秒模拟清理步骤。
        """
        self.sleep(1)
