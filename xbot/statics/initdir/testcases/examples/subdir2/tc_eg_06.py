from lib.testcase import TestCase


class tc_eg_06(TestCase):
    """
    因被 testset.tags.exclude 包含而被跳过的测试用例。

    @用例名称: 因被 testset.tags.exclude 包含而被跳过的测试用例。

    @预置步骤:
        无

    @测试步骤:
        无
        
    @预期结果:
        无
    """

    # 用例最大执行时长（秒）。
    TIMEOUT = 60
    # 用例标签。
    TAGS = ['tag1', 'tag2']

    def setup(self):
        """
        Preset steps.
        """
        self.info('开始执行预置步骤')

    def process(self):
        """
        Test steps.
        """
        self.info('开始执行测试步骤')

    def teardown(self):
        """
        Post steps.
        """
        self.info('开始执行清理步骤')
        self.sleep(1)
