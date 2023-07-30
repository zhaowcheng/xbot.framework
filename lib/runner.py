# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
用例执行器。
"""

import os
import shutil
import traceback

from typing import Union
from threading import Thread
from importlib import import_module
from datetime import datetime
from lib.logger import get_logger
from lib.testbed import TestBed
from lib.testset import TestSet
from lib.testcase import TestCase, TestcaseTimeout
from lib.common import LOG_DIR, LOG_TEMPLATE
from lib.util import render_write, stop_thread


class Runner(object):
    """
    用例执行器。
    """
    def __init__(self) -> None:
        self._logger = get_logger()

    def run(self, testbed: TestBed, testset: TestSet) -> str:
        """
        执行测试套中的测试用例。

        :param testbed: 测试床。
        :param testset: 测试集。
        :return: 本次执行的日志目录。
        """
        logdir = self._make_logdir(testbed)
        for casepath in testset.paths:
            self._logger.info(f' Start: {casepath} '.center(80, '='))
            caselog = self._make_logfile(logdir, casepath)
            try:
                casecls = self._import_case(casepath)
                if testset.tags and set(testset.tags).isdisjoint(casecls.TAGS):
                    self._handle_abnormal_case(
                        'skipped', caselog, testbed, 
                        f'Skipped because dont contain any tag of {testset.tags}.'
                    )
                    self._logger.info(f' End: {casepath} '.center(80, '=') + '\n')
                    continue
            except (ImportError, AttributeError):
                self._handle_abnormal_case(
                    'importerr', caselog, testbed, traceback.format_exc()
                )
                continue
            self._run_case(casecls, testbed, caselog)
            self._logger.info(f' End: {casepath} '.center(80, '=') + '\n')
        return logdir

    def _make_logdir(self, testbed: TestBed) -> str:
        """
        创建日志目录。

        :param testbed: 测试床。
        :return: 日志目录。
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logdir = os.path.join(LOG_DIR, testbed.name, timestamp)
        os.makedirs(logdir)
        return logdir

    def _make_logfile(self, logdir: str, casepath: str) -> str:
        """
        创建日志文件。

        :param logdir: 日志目录。
        :param casepath: 用例路径。
        :return: 日志文件。
        """
        logfile = os.path.normpath(
            os.path.join(logdir, casepath.replace('testcase/', ''))
        ).replace('.py', '.html')
        if not os.path.exists(os.path.dirname(logfile)):
            os.makedirs(os.path.dirname(logfile))
        shutil.copyfile(LOG_TEMPLATE, logfile)
        return logfile

    def _import_case(self, casepath: str) -> TestCase:
        """
        导入测试用例。

        :param casepath: 用例路径。
        :return: 测试用例实例。
        """
        caseid = casepath.split('/')[-1].rstrip('.py')
        modname = casepath.rstrip('.py').replace('/', '.')
        casemod = import_module(modname)
        casecls = getattr(casemod, caseid)
        return casecls

    def _handle_abnormal_case(
        self, 
        reason: Union['importerr', 'skipped'],
        caselog: str, 
        testbed: TestBed,
        message: str
    ) -> None:
        """
        处理非正常用例。

        :param caselog: 用例日志文件。
        :param testbed: 测试床实例。
        :param reason: 错误原因。
        """
        if reason == 'importerr':
            self._logger.error(message)
        elif reason == 'skipped':
            self._logger.warn(message)
        caseid = os.path.basename(caselog).replace('.html', '')
        starttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record = {
            'levelname': {'importerr': 'ERROR', 'skipped': 'WARN'}[reason],
            'asctime': starttime,
            'module': 'runner',
            'threadName': caseid,
            'message': message
        }
        render_write(
            LOG_TEMPLATE,
            caselog,
            caseid=caseid,
            result={'importerr': 'ERROR', 'skipped': 'SKIP'}[reason],
            starttime=starttime,
            endtime=starttime,
            duration='0:00:00',
            testcase=caseid,
            testbed=testbed.content.replace('<','&lt').replace('>','&gt'),
            stage_records={'setup': [record], 'process': [], 'teardown': []}
        )

    def _run_case(
        self, 
        casecls: TestCase, 
        testbed: TestBed, 
        caselog: str
    ) -> None:
        """
        执行测试用例。

        :param casecls: 测试用例类。
        :param testbed: 测试床实例。
        :param caselog: 用例日志文件。
        """
        caseinst = casecls(testbed, caselog)
        t = Thread(target=caseinst.run, name=caseinst.caseid)
        t.start()
        t.join(caseinst.TIMEOUT * 60)
        if t.is_alive():
            stop_thread(t, TestcaseTimeout)
            t.join(60)  # 等待 teardown 结束
