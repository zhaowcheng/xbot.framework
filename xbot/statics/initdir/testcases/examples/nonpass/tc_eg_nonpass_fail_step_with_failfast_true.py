from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_fail_step_with_failfast_true(TestCase):
    """
    在 FAILFAST 为 True 的情况下测试步骤失败。
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
        # 此处失败，由于 FAILFAST=True，将会跳过后续测试步骤并立即执行 teardown。
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
