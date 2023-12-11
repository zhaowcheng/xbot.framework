from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_error_syntax(TestCase):
    """
    存在语法错误的用例。
    """
    TIMEOUT = 60
    FAILFAST = False
    TAGS = ['tag1']

    def setup(self):
        """
        预置步骤。
        """
        self.info('开始执行预置步骤')

    def step1(self):
        """
        测试步骤 1。
        """
        # noinspection PyUnreachableCode
        self.info('开始执行测试步骤 1'  # type: ignore

    def teardown(self):
        """
        清理步骤。
        """
        self.info('开始执行清理步骤')
