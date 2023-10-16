# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Constants.
"""

import os


XBOT_DIR = os.path.abspath('%s/../..' % __file__)

STATICS_DIR = os.path.join(XBOT_DIR, 'static')

INIT_DIR = os.path.join(STATICS_DIR, 'initdir')

LOG_TEMPLATE = os.path.join(STATICS_DIR, 'log_template.html')

REPORT_TEMPLATE = os.path.join(STATICS_DIR, 'report_template.html')

TESTBED_EXAMPLE = os.path.join(INIT_DIR, 'testbeds', 'testbed_example.yml')

TESTSET_TEMPLATE = os.path.join(INIT_DIR, 'testsets', 'testset_template.yml')
