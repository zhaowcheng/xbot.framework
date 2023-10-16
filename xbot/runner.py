# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
TestCase runner.
"""

import os
import shutil
import traceback

from threading import Thread
from importlib import import_module
from datetime import datetime

from xbot.logger import getlogger
from xbot.errors import TestCaseTimeout
from xbot.common import LOG_TEMPLATE
from xbot.util import render_write, stop_thread


logger = getlogger()


class Runner(object):
    """
    TestCase runner.
    """
    def __init__(self):
        pass

    def run(self, testbed, testset):
        """
        Run testcases.

        :param testbed: TestBed instance.
        :param testset: TestSet instance.
        :return: logdir of this execution.
        """
        logdir = self._make_logdir(testbed)
        for casepath in testset.paths:
            logger.info(' Start: %s '.center(80, '='), casepath)
            caselog = self._make_logfile(logdir, casepath)
            try:
                casecls = self._import_case(casepath)
                if testset.tags and set(testset.tags).isdisjoint(casecls.TAGS):
                    self._handle_abnormal_case(
                        'skipped', caselog, testbed, 
                        'Skipped because dont contain any tag of %s.' % testset.tags
                    )
                    logger.info(' End: %s '.center(80, '=') + '\n', casepath)
                    continue
            except (ImportError, AttributeError):
                self._handle_abnormal_case(
                    'importerr', caselog, testbed, traceback.format_exc()
                )
                continue
            self._run_case(casecls, testbed, caselog)
            logger.info(' End: %s '.center(80, '=') + '\n', casepath)
        return logdir

    def _make_logdir(self, testbed):
        """
        Create log directory.

        :param testbed: TestBed instance.
        :return: logdir path.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logdir = os.path.join(os.getcwd(), 'logs', testbed.name, timestamp)
        os.makedirs(logdir)
        return logdir

    def _make_logfile(self, logdir, casepath):
        """
        Create log file.

        :param logdir: logdir path.
        :param casepath: TestCase path.
        :return: logfile path.
        """
        logfile = os.path.normpath(
            os.path.join(logdir, casepath.replace('testcases/', ''))
        ).replace('.py', '.html')
        if not os.path.exists(os.path.dirname(logfile)):
            os.makedirs(os.path.dirname(logfile))
        shutil.copyfile(LOG_TEMPLATE, logfile)
        return logfile

    def _import_case(self, casepath):
        """
        Import testcase module.

        :param casepath: TestCase path.
        :return: TestCase class.
        """
        caseid = casepath.split('/')[-1].rstrip('.py')
        modname = casepath.rstrip('.py').replace('/', '.')
        casemod = import_module(modname)
        casecls = getattr(casemod, caseid)
        return casecls

    def _handle_abnormal_case(self, reason, caselog, testbed, message):
        """
        Handle abnormal case.

        :param caselog: TestCase logfile.
        :param testbed: TestBed instance.
        :param reason: 'importerr' or 'skipped'.
        """
        if reason == 'importerr':
            logger.error(message)
        elif reason == 'skipped':
            logger.warn(message)
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

    def _run_case(self, casecls, testbed, caselog):
        """
        Execute testcase.

        :param casecls: TestCase class.
        :param testbed: TestBed instance.
        :param caselog: TestCase logfile.
        """
        caseinst = casecls(testbed, caselog)
        t = Thread(target=caseinst.run, name=caseinst.caseid)
        t.start()
        t.join(caseinst.TIMEOUT * 60)
        if t.is_alive():
            stop_thread(t, TestCaseTimeout)
            t.join(60)  # wait for teardown to finished.
