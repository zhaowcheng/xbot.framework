import unittest
import logging
import sys
import os
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from io import StringIO

from xbot.logger import (XLogger, StdoutFilter, CaseLogFilter, 
                         CaseLogHandler, ROOT_LOGGER, getlogger)


class TestLogger(unittest.TestCase):
    """
    logger 模块单元测试。
    """
    def test_xlogger_stacklevel(self):
        """
        测试 stacklevel 参数。
        """
        logger = XLogger('test_xlogger')
        strio = StringIO()
        handler = logging.StreamHandler(strio)
        handler.setFormatter(logging.Formatter('%(funcName)s'))
        logger.addHandler(handler)

        def func1(stacklevel):
            logger.info('hello', stacklevel=stacklevel)

        def func2(stacklevel):
            func1(stacklevel)

        func2(stacklevel=1)
        self.assertEqual(strio.getvalue().strip(), 'func1')

        strio.seek(0)
        strio.truncate(0)

        func2(stacklevel=2)
        self.assertEqual(strio.getvalue().strip(), 'func2')

    def test_logging_logger_class(self):
        """
        检查 logging 的 LoggerClass 是否为 XLogger。
        """
        self.assertEqual(logging.getLoggerClass(), XLogger)
        
    def test_stdout_filter(self):
        """
        测试 StdoutFilter。
        """
        filter_ = StdoutFilter()
        self.assertTrue(filter_.filter(logging.makeLogRecord({'levelno': logging.DEBUG })))
        self.assertTrue(filter_.filter(logging.makeLogRecord({'levelno': logging.INFO })))
        self.assertTrue(filter_.filter(logging.makeLogRecord({'levelno': logging.WARN })))
        self.assertFalse(filter_.filter(logging.makeLogRecord({'levelno': logging.ERROR })))
        self.assertFalse(filter_.filter(logging.makeLogRecord({'levelno': logging.CRITICAL })))
            
    def test_case_log_filter(self):
        """
        测试 CaseLogFilter。
        """
        filter_ = CaseLogFilter()
        record = logging.makeLogRecord({ 'threadName': 'test_thread' })
        filter_.name = 'test_thread'
        self.assertTrue(filter_.filter(record))
        filter_.name = 'another_thread'
        self.assertFalse(filter_.filter(record))

    def test_case_log_handler(self):
        """
        测试 CaseLogHandler。
        """
        handler = CaseLogHandler()

        handler.set_stage('stage1')
        record1 = logging.makeLogRecord({ 'message': 'message1' })
        handler.emit(record1)
        self.assertIn('stage1', handler.records)
        self.assertIn(record1.__dict__, handler.records['stage1'])

        handler.set_stage('stage2')
        record2 = logging.makeLogRecord({ 'message': 'message2' })
        handler.emit(record2)
        self.assertIn('stage2', handler.records)
        self.assertIn(record2.__dict__, handler.records['stage2'])
        self.assertNotIn(record2.__dict__, handler.records['stage1'])

    def test_getlogger(self):
        """
        测试 getlogger。
        """
        logger = getlogger('test_module')
        self.assertIsInstance(logger, XLogger)
        self.assertEqual(logger.name, f'{ROOT_LOGGER.name}.test_module')


if __name__ == '__main__':
    unittest.main(verbosity=2)
