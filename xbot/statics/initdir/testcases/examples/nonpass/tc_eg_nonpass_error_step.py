from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_nonpass_error_step(TestCase):
    """
    测试步骤错误的用例。
    """
    TIMEOUT = 60
    FAILFAST = False
    TAGS = ['tag1']

    def setup(self):
        """
        创建列表 self.mylist = [1, 2]
        """
        self.mylist = [1, 2]

    def step1(self):
        """
        访问 self.mylist[2]
        """
        # 此处 error，虽然 FAILFAST = False，但是仍然会跳过后续测试步骤并立即执行清理步骤。
        self.mylist[2]

    def step2(self):
        """
        访问 self.mylist[1]
        """
        self.mylist[1]

    def teardown(self):
        """
        睡 1 秒模拟清理步骤
        """
        self.sleep(1)
