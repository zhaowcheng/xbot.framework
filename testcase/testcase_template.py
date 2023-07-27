# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试用例模块。
"""

from lib.testcase import TestCase


# 类名即为测试用例编号，且应与文件名保持一致。
class tc_xx_xx_01(TestCase):
    r"""
    测试用例简要描述。

    @用例名称：xxx

    @预置条件：
        1.xxxx
        2.xxxx
        3.xxxx

    @测试步骤：
        1.xxxx
        2.xxxx
        3.xxxx
        
    @预期结果：
        1.xxxx
        2.xxxx
        3.xxxx
    """

    # 用例执行最长时间，单位：分钟。
    TIMEOUT = 5
    # 用例标签。
    TAGS = []

    def setup(self) -> None:
        """
        预置条件实现。
        """
        pass

    def process(self) -> None:
        """
        测试步骤实现。
        """
        pass

    def teardown(self) -> None:
        """
        清理步骤实现。
        """
        pass
