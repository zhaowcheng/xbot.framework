# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Testcase base.
"""

import os
import sys
import logging
import traceback
import re
import time
import inspect

from typing import List
from datetime import datetime, timedelta
from importlib import import_module
from threading import Thread

from xbot.framework import logger, common, utils
from xbot.framework.testbed import TestBed
from xbot.framework.testset import TestSet
from xbot.framework.errors import TestCaseTimeout, TestCaseError


class TestCase(object):
    """
    Testcase base.
    """
    # Maximum execution time(seconds), exceeding will be forced to end.
    TIMEOUT = 60
    # If True, skip all unexecuted steps when a failure occurs.
    FAILFAST = True
    # For testcase filtering.
    TAGS = []

    def __init__(self, testbed: TestBed, testset: TestSet, logroot: str):
        """
        :param testbed: TestBed instance.
        :param logroot: testcase logdir.
        """
        self.__testbed = testbed
        self.__testset = testset
        self.__logroot = logroot
        self.__starttime = None
        self.__endtime = None
        self.__duration = None
        self.__result = None
        self.__logger = logger.getlogger(self.caseid)
        self.__loghdlr = logger.CaseLogHandler(logging.DEBUG)
        self.__loghdlr.addFilter(logger.CaseLogFilter(self.caseid))
        self.__loghdlr.setFormatter(logger.FORMATTER)
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
        Testcase filename(without suffix).
        """
        return os.path.basename(self.abspath.replace('.py', ''))
    
    @property
    def abspath(self) -> str:
        """
        Absolute path of testcase file.
        """
        return sys.modules[self.__module__].__file__
    
    @property
    def relpath(self) -> str:
        """
        Relative path of testcase file(startswith `testcases`, split by `/`).
        """
        paths = self.abspath.split(os.path.sep)
        return '/'.join(paths[paths.index('testcases'):])
    
    @property
    def logfile(self) -> str:
        """
        Logfile path(absolute).
        """
        return os.path.normpath(
            os.path.join(self.__logroot, self.relpath.replace('.py', '.html'))
        )
    
    @property
    def sourcecode(self) -> str:
        """
        Source code of testcase.
        """
        return inspect.getsource(import_module(self.__module__))
    
    @property
    def skipped(self) -> bool:
        """
        Whether it is exclued by testset.
        """
        etags = self.__testset.exclude_tags
        itags = self.__testset.include_tags
        return (etags and not set(etags).isdisjoint(self.TAGS)) or \
               (itags and set(itags).isdisjoint(self.TAGS))
    
    @property
    def steps(self) -> List[str]:
        """
        Testcase steps.
        """
        return sorted([n for n in dir(self.__class__) if re.match(r'step\d+', n)])
    
    @property
    def starttime(self) -> datetime:
        """
        Start execution time.
        """
        return self.__starttime

    @property
    def endtime(self) -> datetime:
        """
        End execution time.
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
        Testcase result.
        """
        return self.__result
    
    def debug(self, msg, *args, **kwargs):
        """
        debug level log.
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        info level log.
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """
        warn level log.
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        error level log.
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.error(msg, *args, **kwargs)

    def sleep(self, seconds: float) -> None:
        """
        Sleep for a specified number of seconds.
        """
        self.info('Sleep %s second(s)...' % seconds, stacklevel=3)
        time.sleep(seconds)

    def setup(self) -> None:
        """
        Testcase preset step.
        """
        raise NotImplementedError

    def step1(self) -> None:
        """
        Test step 1(add more in order, e.g. step2, step3, ...).
        At least one step is required.
        """
        raise NotImplementedError

    def teardown(self) -> None:
        """
        Testcase cleanup step.
        """
        raise NotImplementedError
    
    def run(self) -> None:
        """
        Run the current testcase.
        """
        t = Thread(target=self.__run, name=self.caseid)
        t.start()
        t.join(self.TIMEOUT)
        if t.is_alive():
            utils.stop_thread(t, TestCaseTimeout)
            t.join(60)  # 等待 teardown 完成。

    def __run(self) -> None:
        """
        Run the current testcase.
        """
        self.__starttime = datetime.now().replace(microsecond=0)
        if self.skipped:
            self.__loghdlr.set_stage('setup')
            self.__result = 'SKIP'
            self.warn(f'Skipped: self.TAGS={self.TAGS}, ' + 
                      f'testset.tags.include={self.__testset.include_tags}, ' + 
                      f'testset.tags.exclude={self.__testset.exclude_tags}')
        else:
            self.__run_stage('setup')
            if not self.__result:
                for step in self.steps:
                    if not self.__result or (self.__result == 'FAIL' and 
                                             not self.FAILFAST):
                        self.__run_stage(step)
            self.__run_stage('teardown')
        self.__endtime = datetime.now().replace(microsecond=0)
        self.__duration = self.endtime - self.starttime
        self.__result = self.__result or 'PASS'
        self.__dump_log()
        logger.ROOT_LOGGER.removeHandler(self.__loghdlr)

    def __run_stage(self, stage: str) -> None:
        """
        Run the specified stage(setup, step1, ..., stepn, teardown).
        """
        func = getattr(self, stage)
        try:
            self.__loghdlr.set_stage(stage)
            if not callable(func):
                raise TypeError(f'`{stage}` is not callable')
            func()
        except TestCaseTimeout as e:
            self.__result = 'TIMEOUT'
            self.error('TestCaseTimeout: Execution did not '
                       'complete within %s second(s).' % self.TIMEOUT)
        except Exception as e:
            if isinstance(e, TestCaseError):
                self.__result = 'ERROR'
            else:
                self.__result = 'FAIL'
            self.error(traceback.format_exc().strip())

    def __dump_log(self) -> None:
        """
        Save logs to html file.
        """
        os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
        utils.render_write(
            common.LOG_TEMPLATE,
            self.logfile,
            caseid=self.caseid,
            result=self.result,
            starttime=self.starttime.strftime('%Y-%m-%d %H:%M:%S'),
            endtime=self.endtime.strftime('%Y-%m-%d %H:%M:%S'),
            duration=str(self.duration),
            sourcecode=self.sourcecode.replace('<','&lt').replace('>','&gt'),
            testbed=self.testbed.content.replace('<','&lt').replace('>','&gt'),
            stage_records=self.__loghdlr.records
        )


class ErrorTestCase(TestCase):
    """
    Error TestCase.
    """
    def __init__(
        self, 
        caseid: str,
        filepath: str,
        testbed: TestBed, 
        testset: TestSet, 
        logroot: str,
        exc: Exception
    ) -> None:
        """
        :param caseid: testcase id.
        :param filepath: testcase filepath.
        :param testbed: TestBed instance.
        :param testset: TestSet instance.
        :param logroot: testcase logdir.
        :param exc: Exception to be raised.
        """
        self.__caseid = caseid
        self.__filepath = filepath
        self.__exc = exc
        super().__init__(testbed, testset, logroot)

    @property
    def caseid(self) -> str:
        return self.__caseid
    
    @property
    def abspath(self) -> str:
        return self.__filepath
    
    @property
    def skipped(self) -> bool:
        return False
    
    @property
    def sourcecode(self) -> str:
        with open(self.__filepath, encoding='utf8') as f:
            return f.read()
    
    def setup(self) -> None:
        """
        Preset step.
        """
        raise TestCaseError(str(self.__exc)) from None

    def step1(self) -> None:
        """
        Test step 1.
        """
        pass

    def teardown(self) -> None:
        """
        Cleanup step.
        """
        pass