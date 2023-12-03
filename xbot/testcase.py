# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
用例基类。
"""

import os
import sys
import logging
import traceback
import re
import time
import inspect

from typing import Any, List
from datetime import datetime, timedelta
from importlib import import_module

from xbot import logger, common, utils
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.errors import TestCaseTimeout


class TestCase(object):
    """
    用例基类。
    """
    # 最大执行时长（单位：秒），超过该时长将会被强制结束。
    TIMEOUT = 60
    # 如果为 True，当第一个断言失败发生时则跳过所有未执行的 step，直接执行 teardown。
    FAILFAST = True
    # 用例标签。
    TAGS = []

    def __init__(self, testbed: TestBed, testset: TestSet, logfile: str):
        """
        :param testbed: 测试床实例。
        :param logfile: 日志文件路径。
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
        测试床实例。
        """
        return self.__testbed

    @property
    def caseid(self) -> str:
        """
        用例 id（不带后缀的文件名）。
        """
        return os.path.basename(
            sys.modules[self.__module__].__file__.replace('.py', '')
        )
    
    @property
    def steps(self) -> List[str]:
        """
        测试步骤列表。
        """
        return sorted([n for n in dir(self.__class__) if re.match(r'step\d+', n)])
    
    @property
    def starttime(self) -> datetime:
        """
        开始执行时间。
        """
        return self.__starttime

    @property
    def endtime(self) -> datetime:
        """
        结束执行时间。
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
        时间戳：<caseid>_<starttime>
        """
        return '{}_{}'.format(
            self.caseid, self.starttime.strftime('%H%M%S'))

    @property
    def result(self) -> str:
        """
        执行结果。
        """
        return self.__result
    
    def debug(self, msg, *args, **kwargs):
        """
        DEBUG 级别日志。
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        INFO 级别日志。
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """
        WARN 级别日志。
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.warn(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        ERROR 级别日志。
        """
        kwargs['stacklevel'] = kwargs.get('stacklevel', 2)
        self.__logger.error(msg, *args, **kwargs)

    def sleep(self, seconds: float) -> None:
        """
        打印一条日志，然后睡眠指定时长的秒数。
        """
        self.info('Sleep %s second(s)...' % seconds, stacklevel=3)
        time.sleep(seconds)

    def setup(self) -> None:
        """
        用例预置步骤。
        """
        raise NotImplementedError

    def step1(self) -> None:
        """
        用例测试步骤 1，根据需要可继续添加 step2, step3, ...
        一个用例至少需要一个测试步骤，即 step1。
        """
        raise NotImplementedError

    def teardown(self) -> None:
        """
        清理步骤。
        """
        raise NotImplementedError

    def run(self) -> None:
        """
        执行当前用例。
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
        执行用例指定阶段（setup, step1, step2, ..., teardown）。
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
        将用例日志转储到 html 文件。
        """
        utils.render_write(
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
    错误的测试用例。
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
        :param exc: 抛出的异常类型。
        """
        self.__caseid = caseid
        self.__exc = exc
        super().__init__(testbed, testset, logfile)

    @property
    def caseid(self) -> str:
        return self.__caseid
    
    def setup(self) -> None:
        """
        预置步骤。
        """
        raise self.__exc from None

    def step1(self) -> None:
        """
        测试步骤 1。
        """
        pass

    def teardown(self) -> None:
        """
        清理步骤。
        """
        pass