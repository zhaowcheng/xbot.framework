from xbot.util import assertx

from lib.testcase import TestCase


class tc_eg_06(TestCase):
    """
    因被 testset.tags.exclude 包含而被跳过的测试用例。
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1', 'tag2']

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

    def teardown(self):
        """
        Post steps.
        """
        self.info('开始执行清理步骤')
        self.sleep(1)
