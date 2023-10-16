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

from datetime import datetime, timedelta

from xbot import logger, util, common


class TestCase(object):
    """
    TestCase base.
    """

    TIMEOUT = 5  # minute(s)
    TAGS = []

    def __init__(self, testbed, logfile):
        """
        :param testbed: TestBed instance.
        :param logfile: logfile path.
        """
        self.__testbed = testbed
        self.__logfile = logfile
        self.__starttime = None
        self.__endtime = None
        self.__duration = None
        self.__result = None
        self.__logger = logger.get_logger(self.caseid)
        self.__loghdlr = logger.CaseLogHandler(logging.DEBUG)
        self.__loghdlr.addFilter(logger.CaseLogFilter(self.caseid))
        logger.ROOT_LOGGER.addHandler(self.__loghdlr)

    @property
    def testbed(self):
        """
        TestBed instance.
        """
        return self.__testbed

    @property
    def caseid(self):
        """
        TestCase filename without extension.
        """
        return os.path.basename(
            sys.modules[self.__module__].__file__.replace('.py', '')
        )
    
    @property
    def starttime(self):
        """
        Execution start time.
        """
        return self.__starttime

    @property
    def endtime(self):
        """
        Execution end time.
        """
        return self.__endtime

    @property
    def duration(self):
        """
        Execution duration.
        """
        return self.__duration

    @property
    def timestamp(self):
        """
        <caseid>_<starttime>
        """
        return '{}_{}'.format(
            self.caseid, self.starttime.strftime('%H%M%S'))

    @property
    def result(self):
        """
        Execution result.
        """
        return self.__result
    
    def debug(self, msg, *args, **kwargs):
        """
        DEBUG log.
        """
        self.__logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        INFO log.
        """
        self.__logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """
        WARN log.
        """
        self.__logger.warn(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        ERROR log.
        """
        self.__logger.error(msg, *args, **kwargs)

    def assertx(a, op, b):
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
            raise ValueError(f'Invalid operator: {op}')
        if not funcs[op](a, b):
            raise AssertionError(
                f'Expects {a} {op} {b}, but got the opposite.'
            )

    def sleep(self, seconds):
        """
        Sleep with logging.
        """
        self.info(f'Sleep {seconds} second(s)...')
        time.sleep(seconds)

    def setup(self):
        """
        Preset steps.
        """
        raise NotImplementedError

    def process(self):
        """
        Test steps.
        """
        raise NotImplementedError

    def teardown(self):
        """
        Post steps.
        """
        raise NotImplementedError

    def run(self):
        """
        Execute testcase.
        """
        self.__starttime = datetime.now().replace(microsecond=0)
        self.__run_stage('setup')
        if not self.__result:
            self.__run_stage('process')
        self.__run_stage('teardown')
        self.__endtime = datetime.now().replace(microsecond=0)
        self.__duration = self.endtime - self.starttime
        self.__result = self.__result or 'PASS'
        self.__dump_log()
        logger.ROOT_LOGGER.removeHandler(self.__loghdlr)

    def __run_stage(self, stage: str):
        """
        Execute one stage(setup, process, teardown).
        """
        func = {'setup': self.setup,
                'process': self.process,
                'teardown': self.teardown}[stage]
        try:
            self.__loghdlr.stage = stage
            func()
        except TestcaseTimeout:
            self.error(f'TestcaseTimeout: Execution did not '
                       'complete within {self.TIMEOUT} minute(s).')
            self.__result = 'TIMEOUT'
        except Exception as e:
            self.error(traceback.format_exc())
            if isinstance(e, AssertionError):
                self.__result = 'FAIL'
            else:
                self.__result = 'ERROR'

    def __dump_log(self):
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
            testcase=textwrap.dedent(self.__doc__.strip()),
            testbed=self.testbed.content.replace('<','&lt').replace('>','&gt'),
            stage_records=self.__loghdlr.stage_records
        )