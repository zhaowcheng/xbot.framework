# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试用例相关模块。
"""

import os
import sys
import logging
import traceback
import re
import textwrap
import time
import operator

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Container

from lib import logger, util, common
from lib.testbed import TestBed


class TestcaseTimeout(Exception):
    """
    用例执行超时。
    """
    pass


class TestCase(ABC):
    """
    测试用例基类。
    """

    # 用例执行最长时间，单位：分钟。
    TIMEOUT = 5
    # 用例标签。
    TAGS = []

    def __init__(self, testbed: TestBed, logfile: str):
        """
        :param testbed: 测试床实例。
        :param logfile: 日志文件路径。
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
        用例编号（不带后缀的文件名）。
        """
        return os.path.basename(
            sys.modules[self.__module__].__file__.replace('.py', '')
        )
    
    @property
    def starttime(self) -> datetime:
        """
        开始时间。
        """
        return self.__starttime

    @property
    def endtime(self) -> datetime:
        """
        结束时间。
        """
        return self.__endtime

    @property
    def duration(self) -> timedelta:
        """
        执行时长。
        """
        return self.__duration

    @property
    def timestamp(self) -> str:
        """
        时间戳（caseid + starttime）。
        """
        return '{}_{}'.format(
            self.caseid, self.starttime.strftime('%H%M%S'))

    @property
    def result(self) -> str:
        """
        执行结果。
        """
        return self.__result
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """
        DEBUG 日志。
        """
        self.__logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """
        INFO 日志.
        """
        self.__logger.info(msg, *args, **kwargs)

    def warn(self, msg: str, *args, **kwargs) -> None:
        """
        WARN 日志.
        """
        self.__logger.warn(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """
        ERROR 日志.
        """
        self.__logger.error(msg, *args, **kwargs)

    def assertx(a: Any, op: str, b: Any) -> None:
        """
        断言

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

        :param a: 操作对象 a
        :param op: 操作符
        :param b: 操作对象 b
        :raises AssertionError: 断言失败
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

    def sleep(self, seconds: float) -> None:
        """
        带有提示信息的 sleep。
        """
        self.info(f'Sleep {seconds} second(s)...')
        time.sleep(seconds)

    @abstractmethod
    def setup(self) -> None:
        """
        预置步骤。
        """

    @abstractmethod
    def process(self) -> None:
        """
        测试过程。
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        清理步骤。
        """

    def run(self) -> None:
        """
        执行测试用例。
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
        执行测试用例的某个阶段。
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
        保存日志。
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