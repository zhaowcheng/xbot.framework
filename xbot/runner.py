# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
执行器。
"""

import os
import sys

from importlib import import_module
from datetime import datetime
from threading import Thread
from time import sleep

from xbot.logger import getlogger, enable_console_logging
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.testcase import TestCase, ErrorTestCase
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

    def run(self, outfmt: str = 'brief') -> str:
        """
        执行所有用例。

        :param outfmt: 输出模式（verbose/brief）。
        :return: 本次执行的日志根目录。
        """
        fmts = ['verbose', 'brief']
        if outfmt not in fmts:
            raise ValueError(f'`outfmt` must be one of {fmts}')
        if outfmt == 'verbose':
            enable_console_logging()
        logroot = self._make_logroot()
        casecnt = len(self.testset.paths)
        for i, casepath in enumerate(self.testset.paths):
            caseid = casepath.split('/')[-1].replace('.py', '')
            abspath = os.path.abspath(casepath)
            order = f'({i+1}/{casecnt})'
            try:
                casecls = self._import_case(casepath)
                caseinst = casecls(self.testbed, self.testset, logroot)
            except (ImportError, AttributeError, SyntaxError) as e:
                caseinst = ErrorTestCase(caseid, abspath, self.testbed, 
                                         self.testset, logroot, e)
            if outfmt == 'verbose':
                xprint(f'Start: {caseid} {order}'.center(100, '='))
            if outfmt == 'brief':
                timer = self._timer(caseinst, i+1, casecnt)
            caseinst.run()
            if outfmt == 'brief':
                timer.join()
            if outfmt == 'verbose':
                xprint(f'End: {caseid} {order}'.center(100, '='), '\n')
        return logroot
    
    def _timer(self, caseinst: TestCase, seq: int, casecnt: int) -> Thread:
        """
        打印执行时长。
        """
        def _timer():
            order = f'({seq}/{casecnt})'
            order_width = len(f'{casecnt}') * 2 + 3
            fmtstr = f'\r{order:{order_width}}  %-7s  %s  {caseinst.caseid}'
            while not caseinst.endtime or not caseinst.result:
                if not caseinst.starttime:
                    duration = '0:00:00'
                else:
                    duration = datetime.now().replace(microsecond=0) - caseinst.starttime
                xprint(fmtstr % ('RUNNING', duration), end='')
                sleep(1)
            duration = caseinst.endtime - caseinst.starttime
            xprint(fmtstr % (caseinst.result, duration))
        t = Thread(target=_timer)
        t.start()
        return t
        
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
