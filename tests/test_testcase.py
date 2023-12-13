import os
import sys
import unittest
import tempfile
import shutil

from importlib import import_module
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from xbot.testcase import TestCase
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.common import INIT_DIR

sys.path.append(INIT_DIR)

class TestTestCase(unittest.TestCase):
    """
    测试 “测试用例基类”。
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.logroot = tempfile.mkdtemp()
        cls.testbed = TestBed(os.path.join(INIT_DIR, 'testbeds', 'testbed_example.yml'))
        cls.testset = TestSet(os.path.join(INIT_DIR, 'testsets', 'testset_example.yml'))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.logroot)

    def instcase(self, parent: str, caseid: str) -> TestCase:
        """
        实例化测试用例。

        :param parent: 测试用例所在父目录：pass/nonpass。
        :param caseid: 测试用例 id。
        """
        casemod = import_module(f'testcases.examples.{parent}.{caseid}')
        casecls = getattr(casemod, caseid)
        caseinst = casecls(self.testbed, self.testset, self.logroot)
        return caseinst

    def test_tc_eg_pass_get_values_from_testbed(self):
        """
        测试 “从测试床中获取信息并检查的用例“。
        """
        caseid = 'tc_eg_pass_get_values_from_testbed'
        caseinst = self.instcase('pass', caseid)
        caseinst.run()
        self.assertEqual(caseinst.testbed, self.testbed)
        self.assertEqual(caseinst.caseid, caseid)
        self.assertEqual(caseinst.abspath, 
                         os.path.join(INIT_DIR, 
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
        with open(caseinst.abspath) as f:
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

    def test_tc_eg_nonpass_error_step(self):
        """
        测试 “测试步骤错误的用例”。
        """
        caseid = 'tc_eg_nonpass_error_step'
        caseinst = self.instcase('nonpass', caseid)
        self.assertEqual(caseinst.FAILFAST, False)
        caseinst.step2 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'ERROR')
        self.assertEqual(caseinst.skipped, False)
        caseinst.step2.assert_not_called()
        caseinst.teardown.assert_called_once()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_error_setup(self):
        """
        测试 “预置步骤错误的用例”。
        """
        caseid = 'tc_eg_nonpass_error_setup'
        caseinst = self.instcase('nonpass', caseid)
        self.assertEqual(caseinst.FAILFAST, False)
        caseinst.step1 = MagicMock()
        caseinst.step2 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'ERROR')
        self.assertEqual(caseinst.skipped, False)
        caseinst.step1.assert_not_called()
        caseinst.step2.assert_not_called()
        caseinst.teardown.assert_called_once()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_fail_setup(self):
        """
        测试 “预置步骤失败的用例”。
        """
        caseid = 'tc_eg_nonpass_fail_setup'
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

    def test_tc_eg_nonpass_fail_step(self):
        """
        测试 “测试步骤失败的用例”。
        """
        caseid = 'tc_eg_nonpass_fail_step'
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

    def test_tc_eg_nonpass_failfast_false(self):
        """
        测试 “FAILFAST 属性为 False 的用例”。
        """
        caseid = 'tc_eg_nonpass_failfast_false'
        caseinst = self.instcase('nonpass', caseid)
        self.assertEqual(caseinst.FAILFAST, False)
        caseinst.step2 = MagicMock()
        caseinst.step3 = MagicMock()
        caseinst.teardown = MagicMock()
        caseinst.run()
        self.assertEqual(caseinst.result, 'FAIL')
        self.assertEqual(caseinst.skipped, False)
        caseinst.step2.assert_called_once()
        caseinst.step3.assert_called_once()
        caseinst.teardown.assert_called_once()
        self.assertTrue(os.path.exists(caseinst.logfile))

    def test_tc_eg_nonpass_skip_excluded(self):
        """
        测试 “因被 testset.tags.exclude 包含而跳过的测试用例”。
        """
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
        """
        测试 “因不被 testset.tags.include 包含而跳过的测试用例”。
        """
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
        """
        测试 “超时的测试用例”。
        """
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
