# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Constants.
"""

import os


XBOT_DIR = os.path.abspath('%s/../..' % __file__)

TESTCASE_DIR = os.path.join(XBOT_DIR, 'testcase')

TESTBED_DIR = os.path.join(XBOT_DIR, 'testbed')

TESTSET_DIR = os.path.join(XBOT_DIR, 'testset')

LOG_DIR = os.path.join(XBOT_DIR, 'log')

LOG_TEMPLATE = os.path.join(LOG_DIR, 'log_template.html')

REPORT_TEMPLATE = os.path.join(LOG_DIR, 'report_template.html')
