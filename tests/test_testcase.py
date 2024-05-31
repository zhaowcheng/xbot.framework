import os
import sys
import unittest
import tempfile
import shutil
import logging

from importlib import util
from io import StringIO
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from xbot.testcase import TestCase
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.common import INIT_DIR
from xbot.logger import ROOT_LOGGER


class TestTestCase(unittest.TestCase):
    """
    测试 “测试用例基类”。
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.workdir = tempfile.mktemp()
        shutil.copytree(INIT_DIR, cls.workdir)
        sys.path.insert(0, cls.workdir)
        cls.logroot = tempfile.mkdtemp()
        cls.testbed = TestBed(os.path.join(cls.workdir, 'testbeds', 
                                           'testbed_example.yml'))
        cls.testset = TestSet(os.path.join(cls.workdir, 'testsets', 
                                           'testset_example.yml'))
        # 将用例执行时的控制台日志重定向到 StringIO
        for hdlr in ROOT_LOGGER.handlers:
            if isinstance(hdlr, logging.StreamHandler) \
                    and hdlr.stream in [sys.stdout, sys.stderr]:
                hdlr.stream = StringIO()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.logroot)
        sys.path.remove(cls.workdir)

    def instcase(self, parent: str, caseid: str) -> TestCase:
        """
        实例化测试用例。

        通过 importlib.util 来导入，避免批量执行所有单元测试的情况下导入
        了别的测试模块中已导入的用例（import 导入同名模块时会用已导入的缓存）

        :param parent: 测试用例所在父目录：pass/nonpass。
        :param caseid: 测试用例 id。
        """
        name = f'testcases.examples.{parent}.{caseid}'
        path = os.path.join(self.workdir, 'testcases', 'examples',
                            parent, f'{caseid}.py')
        spec = util.spec_from_file_location(name, path)
        casemod = util.module_from_spec(spec)
        sys.modules[name] = casemod
        spec.loader.exec_module(casemod)
        casecls = getattr(casemod, caseid)
        caseinst = casecls(self.testbed, self.testset, self.logroot)
        return caseinst

    def test_tc_eg_pass_get_values_from_testbed(self):
        caseid = 'tc_eg_pass_get_values_from_testbed'
        caseinst = self.instcase('pass', caseid)
        caseinst.run()
        self.assertEqual(caseinst.testbed, self.testbed)
        self.assertEqual(caseinst.caseid, caseid)
        self.assertEqual(caseinst.abspath, 
                         os.path.join(self.workdir, 
                                      'testcases', 
                                      'examples', 
                                      'pass', 
                                      f'{caseid}.py')
                        )
        self.assertEqual(caseinst.relpath, f'testcases/examples/pass/{caseid}.py')
        self.assertEqual(caseinst.logfile,
                         os.path.join(self.logroot, 
                                      'testcases', 
                                      'examples', 
                                      'pass', 
                                      f'{caseid}.html')
                        )
        with open(caseinst.abspath, encoding='utf8') as f:
            self.assertEqual(caseinst.sourcecode, f.read())
        self.assertEqual(caseinst.skipped, False)
        self.assertEqual(caseinst.steps, ['step1', 'step2', 'step3'])
        self.assertIsInstance(caseinst.starttime, datetime)
        self.assertIsInstance(caseinst.endtime, datetime)
        self.assertIsInstance(caseinst.duration, timedelta)
        self.assertTrue(caseinst.endtime > caseinst.starttime)
        self.assertEqual(caseinst.endtime - caseinst.starttime, caseinst.duration)
        self.assertEqual(caseinst.result, 'PASS')
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_fail_setup_with_failfast_false(self):
        caseid = 'tc_eg_nonpass_fail_setup_with_failfast_false'
        caseinst = self.instcase('nonpass', caseid)
        self.assertEqual(caseinst.FAILFAST, False)
        caseinst.step1 = MagicMock()
        caseinst.step2 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'FAIL')
        self.assertEqual(caseinst.skipped, False)
        caseinst.step1.assert_not_called()
        caseinst.step2.assert_not_called()
        caseinst.teardown.assert_called_once()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_fail_setup_with_failfast_true(self):
        caseid = 'tc_eg_nonpass_fail_setup_with_failfast_true'
        caseinst = self.instcase('nonpass', caseid)
        self.assertEqual(caseinst.FAILFAST, True)
        caseinst.step1 = MagicMock()
        caseinst.step2 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'FAIL')
        self.assertEqual(caseinst.skipped, False)
        caseinst.step1.assert_not_called()
        caseinst.step2.assert_not_called()
        caseinst.teardown.assert_called_once()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_fail_step_with_failfast_false(self):
        caseid = 'tc_eg_nonpass_fail_step_with_failfast_false'
        caseinst = self.instcase('nonpass', caseid)
        self.assertEqual(caseinst.FAILFAST, False)
        caseinst.step2 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'FAIL')
        self.assertEqual(caseinst.skipped, False)
        caseinst.step2.assert_called_once()
        caseinst.teardown.assert_called_once()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_fail_step_with_failfast_true(self):
        caseid = 'tc_eg_nonpass_fail_step_with_failfast_true'
        caseinst = self.instcase('nonpass', caseid)
        self.assertEqual(caseinst.FAILFAST, True)
        caseinst.step2 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'FAIL')
        self.assertEqual(caseinst.skipped, False)
        caseinst.step2.assert_not_called()
        caseinst.teardown.assert_called_once()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_skip_excluded(self):
        caseid = 'tc_eg_nonpass_skip_excluded'
        caseinst = self.instcase('nonpass', caseid)
        caseinst.setup = MagicMock()
        caseinst.step1 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'SKIP')
        self.assertEqual(caseinst.skipped, True)
        caseinst.setup.assert_not_called()
        caseinst.step1.assert_not_called()
        caseinst.teardown.assert_not_called()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_skip_not_included(self):
        caseid = 'tc_eg_nonpass_skip_not_included'
        caseinst = self.instcase('nonpass', caseid)
        caseinst.setup = MagicMock()
        caseinst.step1 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'SKIP')
        self.assertEqual(caseinst.skipped, True)
        caseinst.setup.assert_not_called()
        caseinst.step1.assert_not_called()
        caseinst.teardown.assert_not_called()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_timeout(self):
        caseid = 'tc_eg_nonpass_timeout'
        caseinst = self.instcase('nonpass', caseid)
        caseinst.step2 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'TIMEOUT')
        self.assertEqual(caseinst.skipped, False)
        caseinst.step2.assert_not_called()
        caseinst.teardown.assert_called_once()
        self.assertTrue(caseinst.duration.seconds >= caseinst.TIMEOUT)
        self.assertTrue(os.path.exists(caseinst.logfile))


if __name__ == '__main__':
    unittest.main(verbosity=2)
