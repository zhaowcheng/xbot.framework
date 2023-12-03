# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
异常类。
"""


class TestCaseTimeout(Exception):
    """
    Testcase execution timeout.
    """
    pass


class TestSetError(Exception):
    """
    Testset error.
    """
    pass
