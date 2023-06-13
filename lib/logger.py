# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Logging module.
"""

import logging
import inspect
import sys


class StdoutFilter(logging.Filter):
        def filter(self, rec):
            return rec.levelno in (logging.DEBUG, 
                                   logging.INFO, 
                                   logging.WARN)


ROOT_LOGGER = logging.getLogger('xbot')
if not ROOT_LOGGER.hasHandlers():
    ROOT_LOGGER.setLevel('DEBUG')
    stdout = logging.StreamHandler(sys.stdout)
    stdout.addFilter(StdoutFilter())
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setLevel('ERROR')
    formater = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(threadName)s] '
        '[%(module)s] %(message)s')
    stdout.setFormatter(formater)
    stderr.setFormatter(formater)
    ROOT_LOGGER.addHandler(stdout)
    ROOT_LOGGER.addHandler(stderr)


def get_logger(name: str = ''):
    """
    For other modules.
    """
    if name:
        return ROOT_LOGGER.getChild(name)
    else:
        caller = inspect.stack()[1]
        callermod = inspect.getmodulename(caller.filename)
        return ROOT_LOGGER.getChild(callermod)


class ExtraAdapter(logging.LoggerAdapter):
    """
    A logger with an extra field.
    """
    def process(self, msg, kwargs):
        msg = f'[{self.extra}] {msg}' if self.extra else msg
        return msg, kwargs


class CaseLogFilter(logging.Filter):
    """
    TestCase log filter.
    """
    def filter(self, record):
        return self.name == record.threadName


class CaseLogHandler(logging.Handler):
    """
    TestCase log handler.
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
