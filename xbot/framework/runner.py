# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Testcase runner.
"""

import os
import sys

from importlib import import_module
from datetime import datetime
from threading import Thread
from time import sleep

from xbot.framework.logger import getlogger, enable_console_logging
from xbot.framework.testbed import TestBed
from xbot.framework.testset import TestSet
from xbot.framework.testcase import TestCase, ErrorTestCase
from xbot.framework.utils import xprint

sys.path.insert(0, '.')

logger = getlogger(__name__)


class Runner(object):
    """
    Testcase runner.
    """
    def __init__(self, testbed: TestBed, testset: TestSet):
        """
        :param testbed: TestBed instance.
        :param testset: TestSet instance.
        """
        self.testbed = testbed
        self.testset = testset

    def run(self, outfmt: str = 'brief') -> str:
        """
        Run testcases parsed from testset.

        :param outfmt: output format(verbose/brief)
        :return: testcase logdir of this execution.
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
        Flush testcase execution time.
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
        Make testcase logdir of this execution.

        :return: logdir path.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logroot = os.path.join(os.getcwd(), 'logs', self.testbed.name, timestamp)
        os.makedirs(logroot)
        return logroot

    def _import_case(self, casepath: str) -> type:
        """
        Import testcase class.

        :param casepath: testcase filepath(relative).
        :return: testcase class.
        """
        caseid = casepath.split('/')[-1].replace('.py', '')
        modname = casepath.replace('/', '.').replace('.py', '')
        casemod = import_module(modname)
        casecls = getattr(casemod, caseid)
        return casecls
