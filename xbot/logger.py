# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Logging module.
"""

import logging
import inspect
import sys


class ExtraAdapter(logging.LoggerAdapter):
    """
    Logger can logging with extra msg.
    """
    def process(self, msg, kwargs):
        if self.extra:
            msg = '[%s] %s' % (self.extra, msg)
        return msg, kwargs


class StdoutFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, 
                               logging.INFO, 
                               logging.WARN)


class CaseLogFilter(logging.Filter):
    """
    Filter records for testcase.
    """
    def filter(self, record):
        return self.name == record.threadName


class CaseLogHandler(logging.Handler):
    """
    Handler for testcase.
    """
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.stage_records = {
            'setup': [],
            'process': [],
            'teardown': [],
        }
        self.stage = 'setup'

    def emit(self, record):
        self.stage_records[self.stage].append(record.__dict__)


def getlogger(name=None):
    """
    Create logger with name.
    """
    if not name:
        caller = inspect.stack()[1]
        name = inspect.getmodulename(caller.filename)
    return ExtraAdapter(ROOT_LOGGER.getChild(name))


ROOT_LOGGER = logging.getLogger('xbot')


if not ROOT_LOGGER.hasHandlers():
    ROOT_LOGGER.setLevel('DEBUG')
    stdout = logging.StreamHandler(sys.stdout)
    stdout.addFilter(StdoutFilter())
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setLevel('ERROR')
    formater = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(module)s] '
        '[%(threadName)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    stdout.setFormatter(formater)
    stderr.setFormatter(formater)
    ROOT_LOGGER.addHandler(stdout)
    ROOT_LOGGER.addHandler(stderr)

