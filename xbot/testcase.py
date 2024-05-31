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
from threading import Thread

from xbot import logger, common, utils
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.errors import TestCaseTimeout, TestCaseError


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

    def __init__(self, testbed: TestBed, testset: TestSet, logroot: str):
        """
        :param testbed: 测试床实例。
        :param logroot: 日志根目录。
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
        return os.path.basename(self.abspath.replace('.py', ''))
    
    @property
    def abspath(self) -> str:
        """
        用例文件绝对路径。
        """
        return sys.modules[self.__module__].__file__
    
    @property
    def relpath(self) -> str:
        """
        用例文件相对路径。（`testcases`开头，路径分隔符为 `/`）
        """
        paths = self.abspath.split(os.path.sep)
        return '/'.join(paths[paths.index('testcases'):])
    
    @property
    def logfile(self) -> str:
        """
        日志文件路径。
        """
        return os.path.normpath(
            os.path.join(self.__logroot, self.relpath.replace('.py', '.html'))
        )
    
    @property
    def sourcecode(self) -> str:
        """
        用例源码。
        """
        return inspect.getsource(import_module(self.__module__))
    
    @property
    def skipped(self) -> bool:
        """
        是否被跳过。
        """
        etags = self.__testset.exclude_tags
        itags = self.__testset.include_tags
        return (etags and not set(etags).isdisjoint(self.TAGS)) or \
               (itags and set(itags).isdisjoint(self.TAGS))
    
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
        self.__logger.warning(msg, *args, **kwargs)

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
        以线程方式执行当前用例。
        """
        t = Thread(target=self.__run, name=self.caseid)
        t.start()
        t.join(self.TIMEOUT)
        if t.is_alive():
            utils.stop_thread(t, TestCaseTimeout)
            t.join(60)  # 等待 teardown 完成。

    def __run(self) -> None:
        """
        执行当前用例。
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
                    if not self.__result or not self.FAILFAST:
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
        将用例日志转储到 html 文件。
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
    错误的测试用例。
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
        :param caseid: 用例 id。
        :param filepath: 用例文件路径。
        :param testbed: 测试床实例。
        :param testset: 测试集实例。
        :param logroot: 日志根目录。
        :param exc: 抛出的异常类型。
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
        预置步骤。
        """
        raise TestCaseError(str(self.__exc)) from None

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