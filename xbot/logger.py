# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Logging module.
"""

import logging
import os
import sys

from datetime import datetime, timedelta

from xbot.common import LOG_TEMPLATE
from xbot.testbed import TestBed


class XbotLogger(logging.Logger):
    """
    Custom Logger.

    findCaller() and _log() are copied from logging.Logger of Python3.8
    """
    def findCaller(self, stacklevel= 1):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = logging.currentframe()
        #On some versions of IronPython, currentframe() returns None if
        #IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        orig_f = f
        while f and stacklevel > 1:
            f = f.f_back
            stacklevel -= 1
        if not f:
            f = orig_f
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == logging._srcfile:
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break
        return rv

    def _log(self, level, msg, args, exc_info=None, extra=None, stacklevel=1):
        """
        Low-level logging routine which creates a LogRecord and then calls
        all the handlers of this logger to handle the record.
        """
        if logging._srcfile:
            #IronPython doesn't track Python frames, so findCaller raises an
            #exception on some versions of IronPython. We trap it here so that
            #IronPython can use logging.
            try:
                fn, lno, func = self.findCaller(stacklevel)
            except ValueError: # pragma: no cover
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else: # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = self.makeRecord(self.name, level, fn, lno, msg, args,
                                 exc_info, func, extra)
        self.handle(record)


logging.setLoggerClass(XbotLogger)


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
        super(CaseLogHandler, self).__init__(level)
        self.stage_records = {
            'setup': [],
            'process': [],
            'teardown': [],
        }
        self.stage = 'setup'

    def emit(self, record):
        self.stage_records[self.stage].append(record.__dict__)


ROOT_LOGGER = logging.getLogger('xbot')


if not ROOT_LOGGER.handlers:
    ROOT_LOGGER.setLevel('DEBUG')
    stdout = logging.StreamHandler(sys.stdout)
    stdout.addFilter(StdoutFilter())
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setLevel('ERROR')
    formater = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)s] %(message)s'
    )
    stdout.setFormatter(formater)
    stderr.setFormatter(formater)
    ROOT_LOGGER.addHandler(stdout)
    ROOT_LOGGER.addHandler(stderr)


def getlogger(name) -> XbotLogger:
    """
    Create logger with name.
    """
    return ROOT_LOGGER.getChild(name)
