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

    def assert_in(
        self, 
        item: Any, 
        container: Container, 
        extmsg: str = ''
    ) -> None:
        """
        Fail if `item` not in `container`.
        """
        msg = f'{item} not in {container}'
        if extmsg:
            msg += f' ({extmsg})'
        assert item in container, msg

    def assert_not_in(
        self, 
        item: Any, 
        container: Container, 
        extmsg: str = ''
    ) -> None:
        """
        Fail if `item` in `container`.
        """
        msg = f'{item} in {container}'
        if extmsg:
            msg += f' ({extmsg})'
        assert item in container, msg

    def assert_any_in(
        self, 
        items: Container, 
        container: Container, 
        extmsg: str = ''
    ) -> None:
        """
        Fail if none of `items` in `container`.
        """
        msg = f'all of {items} not in {container}'
        if extmsg:
            msg += f' ({extmsg})'
        for i in items:
            if i in container:
                return
        else:
            raise AssertionError(msg)

    def assert_all_in(self, items, container, extemsg=''):
        """items中所有元素都应该被包含于container"""
        errmsg = 'not all of {} in {}'.format(items, container)
        errmsg += '\n' + extemsg if extemsg else ''
        for i in items:
            if i not in container:
                raise AssertionError(errmsg)

    def assert_not_in(self, item, container, extemsg=''):
        """item不应该被包含于container"""
        errmsg = "{} in {}".format(item, container)
        errmsg += '\n' + extemsg if extemsg else ''
        assert item not in container, errmsg

    def assert_equal(self, item1, item2, extemsg=''):
        """item1应该等于item2"""
        errmsg = "{} != {}".format(item1, item2)
        errmsg += '\n' + extemsg if extemsg else ''
        assert item1 == item2, errmsg

    def assert_not_equal(self, item1, item2, extemsg=''):
        """item1应该不等于item2"""
        errmsg = "{} == {}".format(item1, item2)
        errmsg += '\n' + extemsg if extemsg else ''
        assert item1 != item2, errmsg

    def assert_match(self, pattern, string, flags=0, extemsg=''):
        """正则表达式pattern应该匹配string"""
        errmsg = "{} not match {}".format(pattern, string)
        errmsg += '\n' + extemsg if extemsg else ''
        m = re.match(pattern, string, flags)
        assert m is not None, errmsg

    def assert_not_match(self, pattern, string, flags=0, extemsg=''):
        """正则表达式pattern不应该匹配string"""
        errmsg = "{} match {}".format(pattern, string)
        errmsg += '\n' + extemsg if extemsg else ''
        m = re.match(pattern, string, flags)
        assert m is None, errmsg

    def assert_search(self, pattern, string, flags=0, extemsg=''):
        """正在表达式pattern应该在string中搜索到"""
        errmsg = "{} not searched in {}".format(pattern, string)
        errmsg += '\n' + extemsg if extemsg else ''
        m = re.search(pattern, string, flags)
        assert m is not None, errmsg

    def assert_not_search(self, pattern, string, flags=0, extemsg=''):
        """正在表达式pattern不应该在string中搜索到"""
        errmsg = "{} searched in {}".format(pattern, string)
        errmsg += '\n' + extemsg if extemsg else ''
        m = re.search(pattern, string, flags)
        assert m is None, errmsg

    def sleep(self, seconds: float) -> None:
        """
        Sleep with message.
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