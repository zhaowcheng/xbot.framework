from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_error_setup(TestCase):
    """
    预置步骤错误的用例。
    """
    TIMEOUT = 60
    FAILFAST = False
    TAGS = ['tag1']

    def setup(self):
        """
        访问 {'k': 'v'}['x']。
        """
        # setup 出现 error，无论 FAILFAST 是何值，
        # 都会跳过后续测试步骤并立即执行清理步骤。
        {'k': 'v'}['x']

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
