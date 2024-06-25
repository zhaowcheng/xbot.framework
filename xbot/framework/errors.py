# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Exceptions.
"""


class TestCaseTimeout(Exception):
    """
    Testcase execution timeout.
    """
    pass


class TestCaseError(Exception):
    """
    Testcase syntax/format error.
    """
    pass


class TestSetError(Exception):
    """
    Testset syntax/format error.
    """
    pass
