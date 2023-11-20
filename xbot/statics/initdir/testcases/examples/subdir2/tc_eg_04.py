from lib.testcase import TestCase


class tc_eg_04(TestCase):
    """
    错误的测试用例。

    @用例名称: 错误的测试用例。

    @预置步骤:
        1. 创建列表 self.mylist = [1, 2]

    @测试步骤:
        1. 访问 self.mylist[2]
        
    @预期结果:
        无
    """

    # 用例最大执行时长（秒）。
    TIMEOUT = 60
    # 用例标签。
    TAGS = ['tag1']

    def setup(self):
        """
        Preset steps.
        """
        self.info('开始执行预置步骤')
        self.mylist = [1, 2]

    def process(self):
        """
        Test steps.
        """
        # 测试步骤 1
        self.info('开始执行测试步骤 1')
        self.mylist[2]

    def teardown(self):
        """
        Post steps.
        """
        self.info('开始执行清理步骤')
        self.sleep(1)
