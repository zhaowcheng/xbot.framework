# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
公共常量。
"""

import os
import re


XBOT_DIR = os.path.abspath('%s/../..' % __file__)

TESTCASE_DIR = os.path.join(XBOT_DIR, 'testcase')

TESTBED_DIR = os.path.join(XBOT_DIR, 'testbed')

TESTSET_DIR = os.path.join(XBOT_DIR, 'testset')

LOG_DIR = os.path.join(XBOT_DIR, 'log')

LOG_TEMPLATE = os.path.join(LOG_DIR, 'log_template.html')

REPORT_TEMPLATE = os.path.join(LOG_DIR, 'report_template.html')


class REs(object):
    """
    常用正则
    """
    # ansi 控制码
    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
