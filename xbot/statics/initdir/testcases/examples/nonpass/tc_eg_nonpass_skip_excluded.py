from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_skip_excluded(TestCase):
    """
    因被 testset.tags.exclude 包含而跳过的测试用例。
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1', 'tag2']

    def setup(self):
        """
        预置步骤。
        """
        self.info('开始执行预置步骤')

    def step1(self):
        """
        测试步骤 1。
        """
        self.info('开始执行测试步骤 1')

    def teardown(self):
        """
        清理步骤。
        """
        self.info('开始执行清理步骤')
