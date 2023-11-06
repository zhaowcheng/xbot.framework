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
from xbot.util import render_write, stop_thread, xprint


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
            caseid = casepath.split('/')[-1].replace('.py', '')
            self._print_divider('start', caseid)
            caselog = self._make_logfile(logdir, casepath)
            try:
                casecls = self._import_case(casepath)
                if testset.exclude_tags and not set(testset.exclude_tags).isdisjoint(casecls.TAGS):
                    self._handle_abnormal_case(
                        'skipped', caselog, testbed, 
                        'Skipped because contain some tag(s) of exclude_tags:%s.' % str(testset.exclude_tags)
                    )
                    self._print_divider('end', caseid)
                    continue
                if testset.include_tags and set(testset.include_tags).isdisjoint(casecls.TAGS):
                    self._handle_abnormal_case(
                        'skipped', caselog, testbed, 
                        'Skipped because dont contain any tag of include_tags:%s.' % str(testset.include_tags)
                    )
                    self._print_divider('end', caseid)
                    continue
            except (ImportError, AttributeError):
                self._handle_abnormal_case(
                    'importerr', caselog, testbed, traceback.format_exc()
                )
                continue
            self._run_case(casecls, testbed, caselog)
            self._print_divider('end', caseid)
        return logdir

    def _print_divider(self, typ, caseid):
        """
        Print testcase divider.

        :param typ: 'start' or 'end'.
        :param caseid: TestCase id.
        """
        if typ == 'start':
            xprint(' Start: %s '.center(100, '=') % caseid)
        elif typ == 'end':
            xprint(' End: %s '.center(100, '=') % caseid + '\n')
        else:
            raise ValueError('Invalid type: %s' % typ)

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
        caseid = casepath.split('/')[-1].replace('.py', '')
        modname = casepath.replace('/', '.').replace('.py', '')
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
            testcase='',
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
