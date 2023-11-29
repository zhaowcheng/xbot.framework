from xbot.util import assertx

from lib.testcase import TestCase


class tc_eg_04(TestCase):
    """
    错误的测试用例。
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
        # 测试步骤 1
        self.mylist[2]

    def step2(self):
        """
        访问 self.mylist[1]
        """
        # 测试步骤 1
        self.mylist[1]

    def teardown(self):
        """
        睡 1 秒模拟清理步骤
        """
        self.sleep(1)
