# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Exceptions.
"""

class TestbedError(Exception):
    """
    Testbed file error.
    """
    pass


class TestbedSchemaError(Exception):
    """
    Testbed schema file error.
    """
    pass


class TestsetError(Exception):
    """
    Testset file error.
    """
    pass


class TestcaseTimeout(Exception):
    """
    Testcase timeout.
    """
    pass
