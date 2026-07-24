# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Global constants.
"""

import os


XBOT_DIR: str = os.path.abspath('%s/..' % __file__)

STATICS_DIR: str = os.path.join(XBOT_DIR, 'statics')

INIT_DIR: str = os.path.join(STATICS_DIR, 'initdir')

LOG_TEMPLATE: str = os.path.join(STATICS_DIR, 'log_template.html')

REPORT_TEMPLATE: str = os.path.join(STATICS_DIR, 'report_template.html')
