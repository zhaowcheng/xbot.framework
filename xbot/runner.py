# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
TestCase runner.
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
from xbot.util import stop_thread, xprint

sys.path.insert(0, '.')

logger = getlogger('runner')


class Runner(object):
    """
    TestCase runner.
    """
    def __init__(self, testbed: TestBed, testset: TestSet):
        """
        :param testbed: TestBed instance.
        :param testset: TestSet instance.
        """
        self.testbed = testbed
        self.testset = testset

    def run(self) -> str:
        """
        Run testcases.

        :return: logdir of this execution.
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
        Create log directory.

        :param self.testbed: self.testbed instance.
        :return: logdir path.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logdir = os.path.join(os.getcwd(), 'logs', self.testbed.name, timestamp)
        os.makedirs(logdir)
        return logdir

    def _make_logfile(self, logdir: str, casepath: str) -> str:
        """
        Create log file.

        :param logdir: logdir path.
        :param casepath: TestCase path.
        :return: logfile path.
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
        Import testcase module.

        :param casepath: TestCase path.
        :return: TestCase class.
        """
        caseid = casepath.split('/')[-1].replace('.py', '')
        modname = casepath.replace('/', '.').replace('.py', '')
        casemod = import_module(modname)
        casecls = getattr(casemod, caseid)
        return casecls

    def _run_case(self, caseinst: TestCase) -> None:
        """
        Execute testcase.
        """
        t = Thread(target=caseinst.run, name=caseinst.caseid)
        t.start()
        t.join(caseinst.TIMEOUT)
        if t.is_alive():
            stop_thread(t, TestCaseTimeout)
            t.join(60)  # wait for teardown to finished.
