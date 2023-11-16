from lib.testcase import TestCase


class tc_eg_03(TestCase):
    """
    失败的测试用例。

    @用例名称: 失败的测试用例。

    @预置步骤:
        无

    @测试步骤:
        1. 断言 1 == 2；
        
    @预期结果:
        1. 断言失败；
    """

    # 用例最大执行时长（秒）。
    TIMEOUT = 60
    # 用例标签。
    TAGS = ['tag3']

    def setup(self):
        """
        Preset steps.
        """
        self.info('开始执行预置步骤')

    def process(self):
        """
        Test steps.
        """
        # 测试步骤 1
        self.info('开始执行测试步骤 1')
        self.assertx(1, '==', 2)

    def teardown(self):
        """
        Post steps.
        """
        self.info('开始执行清理步骤')
        self.sleep(1)
