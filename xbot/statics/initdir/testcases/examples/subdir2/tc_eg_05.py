from xbot.util import assertx

from lib.testcase import TestCase


class tc_eg_05(TestCase):
    """
    因不被 testset.tags.include 包含而跳过的测试用例。
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = []

    def setup(self):
        """
        Preset steps.
        """
        self.info('开始执行预置步骤')

    def step1(self):
        """
        Test step 1.
        """
        self.info('开始执行测试步骤 1')

    def teardown(self):
        """
        Post steps.
        """
        self.info('开始执行清理步骤')
        self.sleep(1)
