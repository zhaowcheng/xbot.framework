from lib.testcase import TestCase


# 类名将被作为用例编号，且应与文件名保持一致。
class tc_eg_01(TestCase):
    """
    从示例测试床中获取信息并检查。

    @用例名称: 从示例测试床中获取信息并检查。

    @预置步骤:
        无

    @测试步骤:
        1. 获取 `example.key1` 的值；
        2. 获取 `example.key2.key2-1` 的值；
        3. 获取 `example.key3[1]` 的值；
        
    @预期结果:
        1. 值应为 `value1`；
        2. 值应为 `value2-1`；
        3. 值应为 `value3-2`；
    """

    # 用例最大执行时长（分钟）。
    TIMEOUT = 5
    # 用例标签。
    TAGS = ['tag1']

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
        value1 = self.testbed.get('example.key1')
        self.assertx(value1, '==', 'value1')

        # 测试步骤 2
        self.info('开始执行测试步骤 2')
        value2 = self.testbed.get('example.key2.key2-1')
        self.assertx(value2, '==', 'value2-1')
        self.sleep(1)

        # 测试步骤 3
        self.info('开始执行测试步骤 3')
        value3 = self.testbed.get('example.key3[1]')
        self.assertx(value3, '==', 'value3-2')

    def teardown(self):
        """
        Post steps.
        """
        self.info('开始执行清理步骤')
