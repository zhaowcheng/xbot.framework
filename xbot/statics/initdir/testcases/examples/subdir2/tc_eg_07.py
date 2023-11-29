from xbot.util import assertx

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
        Preset steps.
        """
        self.info('开始执行预置步骤')

    def step1(self):
        """
        Test steps.
        """
        self.info('开始执行测试步骤 1')
        self.sleep(3)

    def teardown(self):
        """
        Post steps.
        """
        self.info('开始执行清理步骤')
