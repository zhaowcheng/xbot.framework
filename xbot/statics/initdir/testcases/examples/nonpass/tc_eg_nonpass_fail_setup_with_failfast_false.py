from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_fail_setup_with_failfast_false(TestCase):
    """
    在 FAILFAST 为 False 的情况下预置步骤失败。
    """
    TIMEOUT = 60
    FAILFAST = False
    TAGS = ['tag1']

    def setup(self):
        """
        断言 1 == 0。
        """
        # setup 出现失败，无论 FAILFAST 是何值，
        # 都会跳过后续测试步骤并立即执行清理步骤。
        assertx(1, '==', 0)

    def step1(self):
        """
        断言 1 == 1。
        """
        assertx(1, '==', 1)

    def step2(self):
        """
        断言 2 == 2。
        """
        assertx(2, '==', 2)

    def teardown(self):
        """
        睡 1 秒模拟清理步骤。
        """
        self.sleep(1)
