# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Exceptions.
"""


class TestcaseTimeout(Exception):
    """
    Testcase execution timeout.
    """
    pass


class TestsetError(Exception):
    """
    Testset error.
    """
    pass
