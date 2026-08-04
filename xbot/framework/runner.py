# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Testcase runner.
"""

import os
import sys
import traceback

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
        casecnt = len(self.testset.paths)
        cases = []
        enabled_suites = set()
        for casepath in self.testset.paths:
            caseid = casepath.split('/')[-1].replace('.py', '')
            abspath = os.path.abspath(casepath)
            suites: tuple[type[TestCase], ...] = ()
            try:
                casecls = self._import_case(casepath)
                caseinst = casecls(self.testbed, self.testset, logroot)
                suites = self._suite_chain(casecls)
            except (ImportError, AttributeError, SyntaxError) as exc:
                caseinst = ErrorTestCase(
                    caseid,
                    abspath,
                    self.testbed,
                    self.testset,
                    logroot,
                    exc
                )
            cases.append((caseid, caseinst, suites))
            if not caseinst.skipped:
                enabled_suites.update(suites)

        active_suites: list[type[TestCase]] = []
        failed_suite: type[TestCase] | None = None
        try:
            for i, (caseid, caseinst, suites) in enumerate(cases):
                target_suites = [
                    suite for suite in suites if suite in enabled_suites
                ]
                common = 0
                for active, target in zip(active_suites, target_suites):
                    if active is not target:
                        break
                    common += 1

                for suite in reversed(active_suites[common:]):
                    self._teardown_suite(suite)
                del active_suites[common:]
                if failed_suite not in active_suites:
                    failed_suite = None

                if failed_suite is None:
                    for suite in target_suites[common:]:
                        active_suites.append(suite)
                        if not self._setup_suite(suite):
                            failed_suite = suite
                            break

                order = f'({i+1}/{casecnt})'
                if outfmt == 'verbose':
                    xprint(f'Start: {caseid} {order}'.center(100, '='))
                if outfmt == 'brief':
                    timer = self._timer(caseinst, i+1, casecnt)
                skip_reason = None
                if failed_suite is not None:
                    skip_reason = (
                        f'Suite {failed_suite.__name__} setup failed.'
                    )
                caseinst.run(skip_reason)
                if outfmt == 'brief':
                    timer.join()
                if outfmt == 'verbose':
                    xprint(f'End: {caseid} {order}'.center(100, '='), '\n')
        finally:
            for suite in reversed(active_suites):
                self._teardown_suite(suite)
        return logroot

    def _setup_suite(self, suitecls: type[TestCase]) -> bool:
        """
        Set up a suite and report failure.

        :param suitecls: Suite class.
        :return: True when setup succeeds.
        """
        try:
            self._run_suite_hook(suitecls, 'setup')
            return True
        except Exception:
            logger.error(
                'Suite %s setup failed:\n%s',
                suitecls.__name__,
                traceback.format_exc().strip()
            )
            return False

    def _teardown_suite(self, suitecls: type[TestCase]) -> None:
        """
        Tear down a suite and report failure.

        :param suitecls: Suite class.
        :return: None.
        """
        try:
            self._run_suite_hook(suitecls, 'teardown')
        except Exception:
            logger.error(
                'Suite %s teardown failed:\n%s',
                suitecls.__name__,
                traceback.format_exc().strip()
            )

    def _run_suite_hook(
        self,
        suitecls: type[TestCase],
        stage: str
    ) -> None:
        """
        Run a hook declared by a suite class.

        :param suitecls: Suite class.
        :param stage: Hook name, setup or teardown.
        :return: None.
        """
        hook = vars(suitecls).get(stage)
        if isinstance(hook, classmethod):
            getattr(suitecls, stage)(self.testbed)
    
    def _timer(self, caseinst: TestCase, seq: int, casecnt: int) -> Thread:
        """
        Flush testcase execution time.
        """
        def _timer() -> None:
            order = f'({seq}/{casecnt})'
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
        
    def _make_logroot(self) -> str:
        """
        Make testcase logdir of this execution.

        :return: logdir path.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logroot = os.path.join(os.getcwd(), 'logs', self.testbed.name, timestamp)
        os.makedirs(logroot)
        return logroot

    def _suite_chain(
        self,
        casecls: type[TestCase]
    ) -> tuple[type[TestCase], ...]:
        """
        Get suite classes declared in a testcase MRO.

        :param casecls: Testcase class.
        :return: Suite classes ordered from outermost to innermost.
        """
        mro = casecls.__mro__
        parents = mro[1:mro.index(TestCase)]
        return tuple(
            cls
            for cls in reversed(parents)
            if any(
                isinstance(vars(cls).get(stage), classmethod)
                for stage in ('setup', 'teardown')
            )
        )

    def _import_case(self, casepath: str) -> type[TestCase]:
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
