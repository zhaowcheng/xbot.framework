import os
import sys
import unittest
import tempfile
import shutil
import logging

from importlib import util
from io import StringIO
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from xbot.framework.testcase import TestCase
from xbot.framework.testbed import TestBed
from xbot.framework.testset import TestSet
from xbot.framework.common import INIT_DIR
from xbot.framework.logger import ROOT_LOGGER


class TestTestCase(unittest.TestCase):
    """
    Unit tests for testcase module.
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
        # Hide console output.
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
        Instantiate a testcase class.

        Use importlib.util to import, to avoid importing the cases that have
        been imported in other test modules (importing the same module will
        use the cached one).

        :param parent: The parent directory of the testcase: `pass`/`nonpass`.
        :param caseid: Testcase id.
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
        self.assertEqual(caseinst.steps, ['step1', 'step2', 'step3', 'step4', 'step5'])
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

    def test_external_skip_reason(self) -> None:
        """
        Test an external skip reason.

        :return: None.
        """
        caseid = 'tc_eg_pass_get_values_from_testbed'
        caseinst = self.instcase('pass', caseid)
        caseinst.setup = MagicMock()
        caseinst.step1 = MagicMock()
        caseinst.teardown = MagicMock()
        reason = 'Suite TC_HGDB setup failed.'

        caseinst.run(reason)

        self.assertEqual(caseinst.result, 'SKIP')
        caseinst.setup.assert_not_called()
        caseinst.step1.assert_not_called()
        caseinst.teardown.assert_not_called()
        with open(caseinst.logfile, encoding='utf8') as f:
            self.assertIn(reason, f.read())

    def test_handler_lifecycle_when_log_dump_fails(self) -> None:
        """
        Test handler attachment and cleanup when log dumping fails.

        :return: None.
        """
        caseinst = self.instcase(
            'pass',
            'tc_eg_pass_get_values_from_testbed'
        )
        handler = caseinst._TestCase__loghdlr
        attached_before_run = handler in ROOT_LOGGER.handlers

        with patch('threading.excepthook'):
            with patch(
                'xbot.framework.testcase.utils.render_write',
                side_effect=RuntimeError('dump failed')
            ):
                caseinst.run()

        self.assertFalse(attached_before_run)
        self.assertNotIn(handler, ROOT_LOGGER.handlers)

    def test_same_caseid_log_isolation(self) -> None:
        """
        Test preloaded same-id testcases keep separate stage records.

        :return: None.
        """
        class SameIdCase(TestCase):
            DIRECTORY = ''
            MESSAGE = ''
            TAGS = ['tag1']

            @property
            def caseid(self) -> str:
                """
                Return a shared testcase id.

                :return: Testcase id.
                """
                return 'duplicate'

            @property
            def relpath(self) -> str:
                """
                Return the testcase path.

                :return: Relative testcase path.
                """
                return f'testcases/{self.DIRECTORY}/{self.caseid}.py'

            @property
            def sourcecode(self) -> str:
                """
                Return fake testcase source.

                :return: Testcase source.
                """
                return 'pass'

            def setup(self) -> None:
                """
                Set up the testcase.

                :return: None.
                """
                pass

            def step1(self) -> None:
                """
                Log the testcase marker.

                :return: None.
                """
                self.info(self.MESSAGE)

            def teardown(self) -> None:
                """
                Tear down the testcase.

                :return: None.
                """
                pass

        class LeftCase(SameIdCase):
            DIRECTORY = 'left'
            MESSAGE = 'left-only-message'

        class RightCase(SameIdCase):
            DIRECTORY = 'right'
            MESSAGE = 'right-only-message'

        left = LeftCase(self.testbed, self.testset, self.logroot)
        right = RightCase(self.testbed, self.testset, self.logroot)
        left.run()
        right.run()

        with open(left.logfile, encoding='utf8') as f:
            left_log = f.read()
        with open(right.logfile, encoding='utf8') as f:
            right_log = f.read()
        self.assertIn(LeftCase.MESSAGE, left_log)
        self.assertNotIn(RightCase.MESSAGE, left_log)
        self.assertIn(RightCase.MESSAGE, right_log)
        self.assertNotIn(LeftCase.MESSAGE, right_log)

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
