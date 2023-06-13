# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Main script.
"""

from lib.testbed import TestBed
from lib.testset import TestSet


if __name__ == '__main__':
    tb = TestBed('/Users/wan/CodeProjects/xbot/testbed/testbed_example.xml')
    print(tb.xpath('/testbed/postgresql/host'))
    ts = TestSet('/Users/wan/CodeProjects/xbot/testset/testset_example.xml')