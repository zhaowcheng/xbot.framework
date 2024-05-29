from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_class_name_incorrect(TestCase):
    """
    类名错误（与文件名不一致）的用例。
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
        self.info('开始执行测试步骤 1')

    def teardown(self):
        """
        清理步骤。
        """
        self.info('开始执行清理步骤')
