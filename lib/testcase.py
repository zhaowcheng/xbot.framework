# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Testcase base.
"""

import os
import logging
import traceback
import re
import textwrap
import time

from abc import ABC, abstractmethod
from importlib import import_module
from datetime import datetime, timedelta
from typing import Any, Container

from lib import logger, util, common
from lib.testbed import TestBed
from lib.error import TestcaseTimeout


class TestCase(ABC):
    """
    Testcase base.
    """

    TIMEOUT = 5  # minutes
    TAGS = []

    def __init__(self, testbed: TestBed, logfile: str):
        """
        :param testbed: TestBed instance
        :param logfile: logfile path
        """
        self.testbed = testbed
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
    def caseid(self) -> str:
        """
        Filename without suffix.
        """
        return os.path.basename(
            import_module(self.__module__).__file__.replace('.py', '')
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
        caseid + starttime
        """
        return '{}_{}'.format(
            self.caseid, self.starttime.strftime('%H%M%S'))

    @property
    def result(self) -> str:
        """
        Execution result.
        """
        return self.__result
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """
        DEBUG message.
        """
        self.__logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """
        INFO message.
        """
        self.__logger.info(msg, *args, **kwargs)

    def warn(self, msg: str, *args, **kwargs) -> None:
        """
        WARN message.
        """
        self.__logger.warn(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """
        ERROR message.
        """
        self.__logger.error(msg, *args, **kwargs)


    def sleep(self, seconds: float) -> None:
        """
        带有提示信息的 sleep
        """
        self.info(f'Sleep {seconds} second(s)...')
        time.sleep(seconds)

    @abstractmethod
    def setup(self) -> None:
        """
        Preset steps.
        """

    @abstractmethod
    def process(self) -> None:
        """
        Test steps.
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Recovery steps.
        """

    def run(self) -> None:
        """
        Execute this testcase.
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

    def __run_stage(self, stage: str) -> None:
        """
        Execute the specified stage(setup, process, teardown).
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
            self.__result = 'BLOCK'
        except Exception:
            self.error(traceback.format_exc())
            self.__result = 'FAIL'

    def __dump_log(self):
        """
        Dump the logs to file.
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