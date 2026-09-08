# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Testcase runner.
"""

import os
import sys

from typing import Sequence, Optional
from importlib import import_module
from datetime import datetime
from threading import Thread
from pathlib import PurePosixPath
from time import sleep

from xbot.framework.logger import getlogger, enable_console_logging
from xbot.framework.testbed import TestBed
from xbot.framework.testset import TestSet
from xbot.framework.testcase import TestCase, ErrorTestCase
from xbot.framework.utils import xprint
from xbot.framework.errors import SuperClassError

sys.path.insert(0, '.')

logger = getlogger(__name__)


class Runner(object):
    """
    Testcase runner.
    """
    def __init__(self, testbed: TestBed, testset: TestSet) -> None:
        """
        :param testbed: TestBed instance.
        :param testset: TestSet instance.
        """
        self.testbed: TestBed = testbed
        self.testset: TestSet = testset

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
        casepaths = self.testset.testcases.install + self.testset.testcases.test
        casecnt = len(casepaths)
        instend = len(self.testset.testcases.install) - 1
        setupresults = {}
        for i, casepath in enumerate(casepaths):
            caseid = casepath.split('/')[-1].replace('.py', '')
            caseseq = i + 1
            abspath = os.path.abspath(casepath)
            insting = i <= instend
            try:
                casecls = self._import_case(casepath)
                caseinst = casecls(self.testbed, self.testset, logroot)
            except (ImportError, AttributeError, SyntaxError, SuperClassError) as e:
                caseinst = ErrorTestCase(caseid, abspath, self.testbed, 
                                         self.testset, logroot, e)
            self._run_super_setups(casepath, casecnt, setupresults, logroot, outfmt)
            block_reason = None
            if setupresults[PurePosixPath(casepath).parent] != 'PASS':
                parentpath = PurePosixPath(casepath).parent
                parentcls = self.testset.superclses[parentpath]
                block_reason = f'{parentcls.__name__}.setup was not passed.'
            self._run_case(caseinst, outfmt, casecnt, caseseq, 
                           never_skip=insting, block_reason=block_reason)
            if insting and caseinst.result != 'PASS':
                self._run_super_teardowns(casepath, caseseq, casepaths[:i+1], 
                                          setupresults, logroot, outfmt)
                xprint(f'Execution was interrupted because installation testcase `{casepath}` failed.')
                break
            self._run_super_teardowns(casepath, caseseq, casepaths, 
                                      setupresults, logroot, outfmt)
        return logroot
    
    def _make_logroot(self) -> str:
        """
        Make testcase logdir of this execution.

        :return: logdir path.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logroot = os.path.join(os.getcwd(), 'logs', self.testbed.name, timestamp)
        os.makedirs(logroot)
        return logroot

    def _import_case(self, casepath: str) -> type[TestCase]:
        """
        Import testcase class.

        :param casepath: testcase filepath(relative).
        :return: testcase class.
        """
        caseid = casepath.split('/')[-1].replace('.py', '')
        modname = casepath.replace('/', '.').replace('.py', '')
        # The current directory is definitely the project root, so 
        # relative path imports can be used here. Refer to `main.py:run()`.
        casemod = import_module(modname)
        casecls = getattr(casemod, caseid)
        parentpath = PurePosixPath(casepath).parent
        parentcls = self.testset.superclses[parentpath]
        if casecls.__base__ != parentcls:
            caseclsloc = f'{casepath}:{casecls.__name__}'
            parentclsloc = f'{parentpath}/__init__.py:{parentcls.__name__}'
            raise SuperClassError(f'{caseclsloc} must inherit from {parentclsloc}')
        return casecls

    def _run_super_setups(
        self, 
        casepath: str, 
        casecnt: int,
        setupresults: dict,
        logroot: str,
        outfmt: str
    ) -> None:
        """
        Run setups of all superclasses of the casepath(if needed).
        """
        for parentpath in reversed(PurePosixPath(casepath).parents[:-1]):
            parentcls = self.testset.superclses[parentpath]
            parentinst = parentcls(self.testbed, self.testset, logroot, role='setup')
            grandfatherpath = parentpath.parent
            if parentpath not in setupresults:
                if str(grandfatherpath) == '.' or setupresults[grandfatherpath] == 'PASS':
                    self._run_case(parentinst,
                                   outfmt,
                                   casecnt,
                                   0,
                                   never_skip=True)
                else:
                    grandfathercls = self.testset.superclses[grandfatherpath]
                    self._run_case(parentinst,
                                   outfmt,
                                   casecnt,
                                   0,
                                   never_skip=True,
                                   block_reason=f'{grandfathercls.__name__}.setup was not passed.')
                setupresults[parentpath] = parentinst.result

    def _run_super_teardowns(
        self, 
        casepath: str, 
        caseseq: int,
        casepaths: Sequence, 
        setupresults: dict,
        logroot: str,
        outfmt: str
    ) -> None:
        """
        Run teardowns of all superclasses of the casepath(if needed).
        """
        unexecuted_casepaths = casepaths[caseseq:]
        for parentpath in PurePosixPath(casepath).parents[:-1]:
            parentcls = self.testset.superclses[parentpath]
            parentinst = parentcls(self.testbed, self.testset, logroot, role='teardown')
            for path in unexecuted_casepaths:
                if path.startswith(str(parentpath)):
                    break
            else:
                if setupresults[parentpath] == 'BLOCK':
                    self._run_case(parentinst,
                                   outfmt,
                                   len(casepaths),
                                   0,
                                   never_skip=True,
                                   block_reason=f'{parentcls.__name__}.setup was blocked.')
                else:
                    self._run_case(parentinst,
                                   outfmt,
                                   len(casepaths),
                                   0,
                                   never_skip=True)

    def _run_case(
        self, 
        caseinst: TestCase, 
        outfmt: str, 
        casecnt: int, 
        caseseq: int,
        *args, 
        **kwargs
    ) -> None:
        """
        Run a testcase.
        """
        if casecnt and caseseq:
            order = f' ({caseseq}/{casecnt})'
        else:
            order = ''
        if outfmt == 'verbose':
            xprint(f'Start: {caseinst.caseid}{order}'.center(100, '='))
        if outfmt == 'brief':
            timer = self._timer(caseinst, caseseq, casecnt)
        caseinst.run(*args, **kwargs)
        if outfmt == 'brief':
            timer.join()
        if outfmt == 'verbose':
            xprint(f'End: {caseinst.caseid}{order}'.center(100, '='), '\n')

    def _timer(self, caseinst: TestCase, caseseq: int, casecnt: int) -> Thread:
            """
            Flush testcase execution time.
            """
            def _timer() -> None:
                order = '(^_^)'
                if caseinst and caseseq:
                    order = f'({caseseq}/{casecnt})'
                order_width = len(f'{casecnt}') * 2 + 3
                fmtstr = f'\r{order:{order_width}}  %-7s  %s  {caseinst.caseid}'
                while not caseinst.endtime or not caseinst.result:
                    if not caseinst.starttime:
                        duration: str | object = '0:00:00'
                    else:
                        duration = datetime.now().replace(microsecond=0) - caseinst.starttime
                    xprint(fmtstr % ('RUNNING', duration), end='')
                    sleep(1)
                starttime = caseinst.starttime
                endtime = caseinst.endtime
                if starttime is None or endtime is None:
                    raise RuntimeError('Testcase execution time is incomplete')
                duration = endtime - starttime
                xprint(fmtstr % (caseinst.result, duration))
            t = Thread(target=_timer)
            t.start()
            return t
    