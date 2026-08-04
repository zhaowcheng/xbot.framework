# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
logging.
"""

import logging

from types import TracebackType
from typing import Any, Mapping, MutableMapping, TypeAlias, cast


ExcInfo: TypeAlias = (
    tuple[type[BaseException], BaseException, TracebackType | None]
    | tuple[None, None, None]
)


class XLogger(logging.Logger):
    """
    Custom Logger.
    """
    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: tuple[Any, ...] | Mapping[str, Any],
        exc_info: (
            ExcInfo | None
        ),
        func: str | None = None,
        extra: Mapping[str, object] | None = None,
        sinfo: str | None = None
    ) -> logging.LogRecord:
        """
        Copy from super class and remove `raise KeyError` line.
        """
        factory = logging.getLogRecordFactory()
        rv = factory(name, level, fn, lno, msg, args,
                     exc_info, func, sinfo)
        if extra is not None:
            for key in extra:
                rv.__dict__[key] = extra[key]
        return rv


logging.setLoggerClass(XLogger)


class StdoutFilter(logging.Filter):
    def filter(self, rec: logging.LogRecord) -> bool:
        return rec.levelno in (logging.DEBUG, 
                               logging.INFO, 
                               logging.WARN)


class CaseLogFilter(logging.Filter):
    """
    Testcase log filter.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        return self.name == record.threadName


class CaseLogHandler(logging.Handler):
    """
    Testcase log handler.
    """
    def __init__(self, level: int | str = logging.NOTSET) -> None:
        super(CaseLogHandler, self).__init__(level)
        self.records: dict[str | None, list[dict[str, Any]]] = {}
        self.stage: str | None = None

    def set_stage(self, stage: str) -> None:
        self.stage = stage
        if self.stage not in self.records:
            self.records[self.stage] = []

    def emit(self, record: logging.LogRecord) -> None:
        if self.stage not in self.records:
            self.records[self.stage] = []
        self.format(record)
        self.records[self.stage].append(record.__dict__)


class ExtraAdapter(logging.LoggerAdapter):
    """
    Extra content for log message.
    """
    def process(
        self,
        msg: object,
        kwargs: MutableMapping[str, Any]
    ) -> tuple[object, MutableMapping[str, Any]]:
        if self.extra is not None and 'prefix' in self.extra:
            msg = f'[{self.extra["prefix"]}] {msg}'
        return msg, kwargs


ROOT_LOGGER: logging.Logger = logging.getLogger('xbot')
ROOT_LOGGER.setLevel('DEBUG')
FORMATTER: logging.Formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)s] %(message)s'
)
console_logging_enabled: bool = False


def enable_console_logging() -> None:
    """
    Add stream handler(sys.stdout) to root logger.
    """
    global console_logging_enabled
    if console_logging_enabled:
        return
    stdout = logging.StreamHandler(sys.stdout)
    stdout.addFilter(StdoutFilter())
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setLevel('ERROR')
    stdout.setFormatter(FORMATTER)
    stderr.setFormatter(FORMATTER)
    ROOT_LOGGER.addHandler(stdout)
    ROOT_LOGGER.addHandler(stderr)
    console_logging_enabled = True


def getlogger(name: str) -> XLogger:
    """
    Get child logger of root logger.
    """
    return cast(XLogger, ROOT_LOGGER.getChild(name))
