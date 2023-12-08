# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
执行器。
"""

import os
import sys

from importlib import import_module
from datetime import datetime

from xbot.logger import getlogger
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.testcase import ErrorTestCase
from xbot.utils import xprint

sys.path.insert(0, '.')

logger = getlogger('runner')


class Runner(object):
    """
    执行器。
    """
    def __init__(self, testbed: TestBed, testset: TestSet):
        """
        :param testbed: 测试床实例。
        :param testset: 测试套实例。
        """
        self.testbed = testbed
        self.testset = testset

    def run(self) -> str:
        """
        执行所有用例。

        :return: 本次执行的日志根目录。
        """
        logroot = self._make_logroot()
        casecnt = len(self.testset.paths)
        for i, casepath in enumerate(self.testset.paths):
            caseid = casepath.split('/')[-1].replace('.py', '')
            xprint(f'Start: {caseid} ({i+1}/{casecnt})'.center(100, '='))
            try:
                casecls = self._import_case(casepath)
                caseinst = casecls(self.testbed, self.testset, logroot)
            except (ImportError, AttributeError) as e:
                caseinst = ErrorTestCase(self.testbed, self.testset, 
                                         logroot, caseid, e)
            caseinst.run()
            xprint(f'End: {caseid} ({i+1}/{casecnt})'.center(100, '='), '\n')
        return logroot
        
    def _make_logroot(self) -> str:
        """
        创建本次执行的日志根目录。

        :return: 目录路径。
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logroot = os.path.join(os.getcwd(), 'logs', self.testbed.name, timestamp)
        os.makedirs(logroot)
        return logroot

    def _import_case(self, casepath: str) -> type:
        """
        导入用例。

        :param casepath: 用例相对路径。
        :return: 用例类。
        """
        caseid = casepath.split('/')[-1].replace('.py', '')
        modname = casepath.replace('/', '.').replace('.py', '')
        casemod = import_module(modname)
        casecls = getattr(casemod, caseid)
        return casecls
