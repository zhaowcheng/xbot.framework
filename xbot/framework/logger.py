# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
logging.
"""

import logging
import os
import sys


class XLogger(logging.Logger):
    """
    Custom Logger.
    """
    def findCaller(self, stacklevel= 1):
        """
        Copy from Python3.8
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
        Copy from Python3.8
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

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info,
                   func=None, extra=None, sinfo=None):
        """
        Copy from super class and remove `raise KeyError` line.
        """
        rv = logging._logRecordFactory(name, level, fn, lno, msg, args, 
                                       exc_info, func,sinfo)
        if extra is not None:
            for key in extra:
                rv.__dict__[key] = extra[key]
        return rv


logging.setLoggerClass(XLogger)


class StdoutFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, 
                               logging.INFO, 
                               logging.WARN)


class CaseLogFilter(logging.Filter):
    """
    Testcase log filter.
    """
    def filter(self, record):
        return self.name == record.threadName


class CaseLogHandler(logging.Handler):
    """
    Testcase log handler.
    """
    def __init__(self, level=logging.NOTSET):
        super(CaseLogHandler, self).__init__(level)
        self.records = {}
        self.stage = None

    def set_stage(self, stage: str):
        self.stage = stage
        if self.stage not in self.records:
            self.records[self.stage] = []

    def emit(self, record):
        if self.stage not in self.records:
            self.records[self.stage] = []
        self.format(record)
        self.records[self.stage].append(record.__dict__)


class ExtraAdapter(logging.LoggerAdapter):
    """
    Extra content for log message.
    """
    def process(self, msg, kwargs):
        if 'prefix' in self.extra:
            msg = f'[{self.extra["prefix"]}] {msg}'
        return msg, kwargs


ROOT_LOGGER = logging.getLogger('xbot')
ROOT_LOGGER.setLevel('DEBUG')
FORMATTER = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s] %(message)s'
)


def enable_console_logging() -> None:
    """
    Add stream handler(sys.stdout) to root logger.
    """
    if 'console_logging_enabled' in globals():
        return
    stdout = logging.StreamHandler(sys.stdout)
    stdout.addFilter(StdoutFilter())
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setLevel('ERROR')
    stdout.setFormatter(FORMATTER)
    stderr.setFormatter(FORMATTER)
    ROOT_LOGGER.addHandler(stdout)
    ROOT_LOGGER.addHandler(stderr)
    global console_logging_enabled
    console_logging_enabled = True


def getlogger(name) -> XLogger:
    """
    Get child logger of root logger.
    """
    return ROOT_LOGGER.getChild(name)
