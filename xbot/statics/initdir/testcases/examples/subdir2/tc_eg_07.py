from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_07(TestCase):
    """
    超时的测试用例。
    """
    TIMEOUT = 2
    FAILFAST = True
    TAGS = ['tag1']

    def setup(self):
        """
        预置步骤。
        """
        self.info('开始执行预置步骤')

    def step1(self):
        """
        睡眠 3 秒。
        """
        self.sleep(3)

    def teardown(self):
        """
        清理步骤。
        """
        self.info('开始执行清理步骤')
