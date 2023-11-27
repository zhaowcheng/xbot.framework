# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
TestCase base.
"""

import os
import sys
import logging
import traceback
import re
import textwrap
import time
import operator

from typing import Any
from datetime import datetime, timedelta

from xbot import logger, util, common
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.errors import TestCaseTimeout


class TestCase(object):
    """
    TestCase base.
    """

    # Max execution time(seconds).
    TIMEOUT = 60
    # Can it be executed in parallel.
    PARALLEL = False
    # Testcase tags.
    TAGS = []

    def __init__(self, testbed: TestBed, testset: TestSet, logfile: str):
        """
        :param testbed: TestBed instance.
        :param logfile: logfile path.
        """
        self.__testbed = testbed
        self.__testset = testset
        self.__logfile = logfile
        self.__starttime = None
        self.__endtime = None
        self.__duration = None
        self.__result = None
        self.__logger = logger.getlogger(self.caseid)
        self.__loghdlr = logger.CaseLogHandler(logging.DEBUG)
        self.__loghdlr.addFilter(logger.CaseLogFilter(self.caseid))
        logger.ROOT_LOGGER.addHandler(self.__loghdlr)

    @property
    def testbed(self) -> TestBed:
        """
        TestBed instance.
        """
        return self.__testbed

    @property
    def caseid(self) -> str:
        """
        TestCase filename without extension.
        """
        return os.path.basename(
            sys.modules[self.__module__].__file__.replace('.py', '')
        )
    
    @property
    def starttime(self) -> datetime:
        """
        Execution start time.
        """
        return self.__starttime

    @property
    def endtime(self) -> datetime:
        """
        Execution end time.
        """
        return self.__endtime

    @property
    def duration(self) -> timedelta:
        """
        Execution duration.
        """
        return self.__duration

    @property
    def timestamp(self) -> str:
        """
        <caseid>_<starttime>
        """
        return '{}_{}'.format(
            self.caseid, self.starttime.strftime('%H%M%S'))

    @property
    def result(self) -> str:
        """
        Execution result.
        """
        return self.__result
    
    def debug(self, msg, *args, **kwargs):
        """
        DEBUG log.
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        INFO log.
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """
        WARN log.
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.warn(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        ERROR log.
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.error(msg, *args, **kwargs)

    def assertx(self, a: Any, op: str, b: Any) -> None:
        """
        Assertion.

        >>> assertx(1, '==', 1)
        >>> assertx(1, '!=', 2)
        >>> assertx(1, '>', 0)
        >>> assertx(1, '>=', 1)
        >>> assertx(1, '<', 2)
        >>> assertx(1, '<=', 1)
        >>> assertx(1, 'in', [1, 2, 3])
        >>> assertx(1, 'not in', [2, 3, 4])
        >>> assertx(1, 'is', 1)
        >>> assertx(1, 'is not', 2)
        >>> assertx('abc', 'match', r'^[a-z]+$')
        >>> assertx('abc', 'not match', r'^[0-9]+$')
        >>> assertx('abc', 'search', r'[a-z]')
        >>> assertx('abc', 'not search', r'[0-9]')

        :param a: Operation object a.
        :param op: Operator.
        :param b: Operation object b.
        :raises AssertionError: Assertion failed.
        """
        funcs = {
            '==': operator.eq,
            '!=': operator.ne,
            '>': operator.gt,
            '>=': operator.ge,
            '<': operator.lt,
            '<=': operator.le,
            'in': lambda a, b: operator.contains(b, a),
            'not in': lambda a, b: not operator.contains(b, a),
            'is': operator.is_,
            'is not': operator.is_not,
            'match': lambda a, b: re.match(b, a),
            'not match': lambda a, b: not re.match(b, a),
            'search': lambda a, b: re.search(b, a),
            'not search': lambda a, b: not re.search(b, a)
        }
        if op not in funcs:
            raise ValueError('Invalid operator: %s', op)
        if not funcs[op](a, b):
            raise AssertionError('%s %s %s' % (a, op, b))
        else:
            self.info('AssertionOK: %s %s %s', a, op, b, stacklevel=3)

    def sleep(self, seconds: float) -> None:
        """
        Sleep with logging.
        """
        self.info('Sleep %s second(s)...' % seconds, stacklevel=3)
        time.sleep(seconds)

    def setup(self) -> None:
        """
        Preset steps.
        """
        raise NotImplementedError

    def process(self) -> None:
        """
        Test steps.
        """
        raise NotImplementedError

    def teardown(self) -> None:
        """
        Post steps.
        """
        raise NotImplementedError

    def run(self) -> None:
        """
        Execute testcase.
        """
        self.__starttime = datetime.now().replace(microsecond=0)
        etags = self.__testset.exclude_tags
        itags = self.__testset.include_tags
        if etags and not set(etags).isdisjoint(self.TAGS):
            self.warn(f'Skipped: self.TAGS={self.TAGS}, testset.tags.exclude={etags}')
            self.__result = 'SKIP'
        elif itags and set(itags).isdisjoint(self.TAGS):
            self.warn(f'Skipped: self.TAGS={self.TAGS}, testset.tags.include={itags}')
            self.__result = 'SKIP'
        else:
            self.__run_stage('setup')
            if not self.__result:
                self.__run_stage('process')
            self.__run_stage('teardown')
        self.__endtime = datetime.now().replace(microsecond=0)
        self.__duration = self.endtime - self.starttime
        self.__result = self.__result or 'PASS'
        self.__dump_log()
        logger.ROOT_LOGGER.removeHandler(self.__loghdlr)

    def __run_stage(self, stage: str) -> None:
        """
        Execute one stage(setup, process, teardown).
        """
        func = {'setup': self.setup,
                'process': self.process,
                'teardown': self.teardown}[stage]
        try:
            self.__loghdlr.stage = stage
            func()
        except TestCaseTimeout:
            self.error('TestCaseTimeout: Execution did not '
                       'complete within %s second(s).' % self.TIMEOUT)
            self.__result = 'TIMEOUT'
        except Exception as e:
            self.error(traceback.format_exc())
            if isinstance(e, AssertionError):
                self.__result = 'FAIL'
            else:
                self.__result = 'ERROR'

    def __dump_log(self) -> None:
        """
        Dump testcase log.
        """
        util.render_write(
            common.LOG_TEMPLATE,
            self.__logfile,
            caseid=self.caseid,
            result=self.result,
            starttime=self.starttime.strftime('%Y-%m-%d %H:%M:%S'),
            endtime=self.endtime.strftime('%Y-%m-%d %H:%M:%S'),
            duration=str(self.duration),
            testcase=textwrap.dedent(' ' * 4 + self.__doc__.strip()),
            testbed=self.testbed.content.replace('<','&lt').replace('>','&gt'),
            stage_records=self.__loghdlr.stage_records
        )


class ErrorTestCase(TestCase):
    """
    Construct an error testcase for runner.
    """
    def __init__(
        self, 
        testbed: TestBed, 
        testset: TestSet, 
        logfile: str,
        caseid: str,
        exc: Exception
    ) -> None:
        """
        :param exc: Exception instance to raise.
        """
        self.__caseid = caseid
        self.__exc = exc
        super().__init__(testbed, testset, logfile)

    @property
    def caseid(self) -> str:
        return self.__caseid
    
    def setup(self) -> None:
        """
        Preset steps.
        """
        raise self.__exc from None

    def process(self) -> None:
        """
        Test steps.
        """
        pass

    def teardown(self) -> None:
        """
        Post steps.
        """
        pass