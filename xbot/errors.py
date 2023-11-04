# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Exceptions.
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
