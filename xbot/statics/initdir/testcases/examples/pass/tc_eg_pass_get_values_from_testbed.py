from xbot.utils import assertx

from lib.testcase import TestCase


# 类名将被作为用例编号，且应与文件名保持一致。
class tc_eg_pass_get_values_from_testbed(TestCase):
    """
    从示例测试床中获取信息并检查。
    """
    # 用例最大执行时长（秒）。
    TIMEOUT = 60
    # 当第一个 FAIL(断言失败) 出现时是否立即停止用例执行
    FAILFAST = True
    # 用例标签。
    TAGS = ['tag1']

    def setup(self):
        """
        无
        """
        pass

    def step1(self):
        """
        获取 `example.key1` 的值并检查，值应为 `value1`。
        """
        value1 = self.testbed.get('example.key1')
        assertx(value1, '==', 'value1')

    def step2(self):
        """
        获取 `example.key2.key2-1` 的值并检查，值应为 `value2-1`。
        """
        value2 = self.testbed.get('example.key2.key2-1')
        assertx(value2, '==', 'value2-1')

    def step3(self):
        """
        获取 `example.key3[1]` 的值并检查，值应为 `value3-2`。
        """
        value3 = self.testbed.get('example.key3[1]')
        assertx(value3, '==', 'value3-2')

    def teardown(self):
        """
        睡 1 秒模拟清理步骤。
        """
        self.sleep(1)
