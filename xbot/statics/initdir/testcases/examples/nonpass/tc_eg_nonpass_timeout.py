from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_timeout(TestCase):
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
        # 此处因超时而 error，会被强行终止，然后立即执行清理步骤。
        self.sleep(3)

    def step2(self):
        """
        测试步骤 2。
        """
        self.info('开始执行测试步骤 2')

    def teardown(self):
        """
        清理步骤。
        """
        self.info('开始执行清理步骤')
