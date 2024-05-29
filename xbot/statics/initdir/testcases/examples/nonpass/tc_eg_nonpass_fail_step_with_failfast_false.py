from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_fail_step_with_failfast_false(TestCase):
    """
    在 FAILFAST 为 False 的情况下测试步骤失败。
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
        断言 1 == 2。
        """
        # 此处失败，由于 FAILFAST=False，将会继续执行后续测试步骤。
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
