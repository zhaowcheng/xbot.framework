# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
执行器。
"""

import os
import sys
import shutil

from threading import Thread
from importlib import import_module
from datetime import datetime

from xbot.logger import getlogger
from xbot.errors import TestCaseTimeout
from xbot.common import LOG_TEMPLATE
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.testcase import TestCase, ErrorTestCase
from xbot.utils import stop_thread, xprint

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
        logdir = self._make_logdir()
        casecnt = len(self.testset.paths)
        for i, casepath in enumerate(self.testset.paths):
            caseid = casepath.split('/')[-1].replace('.py', '')
            xprint(f'Start: {caseid} ({i+1}/{casecnt})'.center(100, '='))
            caselog = self._make_logfile(logdir, casepath)
            try:
                casecls = self._import_case(casepath)
                caseinst = casecls(self.testbed, self.testset, caselog)
            except (ImportError, AttributeError) as e:
                caseinst = ErrorTestCase(self.testbed, self.testset, 
                                         caselog, caseid, e)
            self._run_case(caseinst)
            xprint(f'End: {caseid} ({i+1}/{casecnt})'.center(100, '='), '\n')
        return logdir
        
    def _make_logdir(self) -> str:
        """
        创建日志根目录。

        :return: 日志目录路径。
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logdir = os.path.join(os.getcwd(), 'logs', self.testbed.name, timestamp)
        os.makedirs(logdir)
        return logdir

    def _make_logfile(self, logdir: str, casepath: str) -> str:
        """
        创建用例日志文件。

        :param logdir: 日志根目录。
        :param casepath: 用例相对路径。
        :return: 用例日志文件路径。
        """
        logfile = os.path.normpath(
            os.path.join(logdir, casepath.replace('testcases/', ''))
        ).replace('.py', '.html')
        if not os.path.exists(os.path.dirname(logfile)):
            os.makedirs(os.path.dirname(logfile))
        shutil.copyfile(LOG_TEMPLATE, logfile)
        return logfile

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

    def _run_case(self, caseinst: TestCase) -> None:
        """
        执行指定用例。
        """
        t = Thread(target=caseinst.run, name=caseinst.caseid)
        t.start()
        t.join(caseinst.TIMEOUT)
        if t.is_alive():
            stop_thread(t, TestCaseTimeout)
            t.join(60)  # 登台 teardown 完成。