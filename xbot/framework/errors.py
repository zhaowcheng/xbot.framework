# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
异常类。
"""


class TestCaseTimeout(Exception):
    """
    测试用例执行超时。
    """
    pass


class TestCaseError(Exception):
    """
    测试用例错误。
    """
    pass


class TestSetError(Exception):
    """
    测试套错误。
    """
    pass
