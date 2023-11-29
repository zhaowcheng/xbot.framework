# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
TestCase base.
"""

import os
import sys
import logging
import traceback
import re
import time
import operator
import inspect

from typing import Any, List
from datetime import datetime, timedelta
from importlib import import_module

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
    # Stop the test run on the first fail.
    FAILFAST = True
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
    def steps(self) -> List[str]:
        """
        Test steps.
        """
        return sorted([n for n in dir(self.__class__) if re.match(r'step\d+', n)])
    
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

    def step1(self) -> None:
        """
        Test step 1, you can add step2, step3, etc., these 
        steps will be executed in the order of their names, 
        a testcase requires at lease one step.
        """
        raise NotImplementedError

    def teardown(self) -> None:
        """
        Cleanup steps.
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
            self.__loghdlr.set_stage('setup')
            self.__result = 'SKIP'
            self.warn(f'Skipped: self.TAGS={self.TAGS}, testset.tags.exclude={etags}')
        elif itags and set(itags).isdisjoint(self.TAGS):
            self.__loghdlr.set_stage('setup')
            self.__result = 'SKIP'
            self.warn(f'Skipped: self.TAGS={self.TAGS}, testset.tags.include={itags}')
        else:
            self.__run_stage('setup')
            if not self.__result:
                for step in self.steps:
                    if not self.__result or (self.__result == 'FAIL' and 
                                             self.FAILFAST == False):
                        self.__run_stage(step)
            self.__run_stage('teardown')
        self.__endtime = datetime.now().replace(microsecond=0)
        self.__duration = self.endtime - self.starttime
        self.__result = self.__result or 'PASS'
        self.__dump_log()
        logger.ROOT_LOGGER.removeHandler(self.__loghdlr)

    def __run_stage(self, stage: str) -> None:
        """
        Execute one stage(setup, step1, teardown, etc).
        """
        func = getattr(self, stage)
        try:
            self.__loghdlr.set_stage(stage)
            if not callable(func):
                raise TypeError(f'`{stage}` is not callable')
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
            sourcecode=inspect.getsource(import_module(self.__module__)),
            testbed=self.testbed.content.replace('<','&lt').replace('>','&gt'),
            stage_records=self.__loghdlr.records
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

    def step1(self) -> None:
        """
        Test step 1.
        """
        pass

    def teardown(self) -> None:
        """
        Post steps.
        """
        pass