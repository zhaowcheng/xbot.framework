import os
import sys
import re
import unittest
import tempfile
import shutil
import logging

from io import StringIO
from typing import ClassVar
from unittest.mock import MagicMock, patch

from xbot.framework import utils
from xbot.framework.testbed import TestBed
from xbot.framework.testset import TestSet
from xbot.framework.testcase import TestCase
from xbot.framework.runner import Runner
from xbot.framework.common import INIT_DIR
from xbot.framework.logger import ROOT_LOGGER


class SuiteTestCase(TestCase):
    """
    Minimal testcase used by suite runner tests.
    """

    EVENTS: ClassVar[list[str]] = []
    SKIPPED: ClassVar[bool] = False

    def __init__(
        self,
        testbed: TestBed,
        testset: TestSet,
        logroot: str
    ) -> None:
        """
        Initialize a fake testcase.

        :param testbed: TestBed instance.
        :param testset: TestSet instance.
        :param logroot: Testcase log root.
        :return: None.
        """
        self._caseid = self.__class__.__name__

    @property
    def caseid(self) -> str:
        """
        Return the fake testcase id.

        :return: Testcase id.
        """
        return self._caseid

    @property
    def skipped(self) -> bool:
        """
        Return whether the testcase is skipped.

        :return: Skip state.
        """
        return self.SKIPPED

    def run(self, skip_reason: str | None = None) -> None:
        """
        Record testcase execution.

        :param skip_reason: External skip reason.
        :return: None.
        """
        self.EVENTS.append(
            f'{self.caseid}.skip:{skip_reason}'
            if skip_reason
            else self.caseid
        )


class TestRunner(unittest.TestCase):
    """
    Unit tests for runner module.
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.workdir = tempfile.mktemp()
        cls.logroot = tempfile.mkdtemp()
        shutil.copytree(INIT_DIR, cls.workdir)
        cls.runner = Runner(
            TestBed(os.path.join(cls.workdir, 'testbeds', 'testbed_example.yml')),
            TestSet(os.path.join(cls.workdir, 'testsets', 'testset_example.yml'))
        )
        # Hide console output.
        for hdlr in ROOT_LOGGER.handlers:
            if isinstance(hdlr, logging.StreamHandler) \
                    and hdlr.stream in [sys.stdout, sys.stderr]:
                hdlr.stream = StringIO()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.workdir)
        shutil.rmtree(cls.logroot)

    def run_suite_cases(
        self,
        *caseclasses: type[SuiteTestCase]
    ) -> list[str]:
        """
        Run fake testcase classes through Runner.

        :param caseclasses: Fake testcase classes in execution order.
        :return: Recorded lifecycle events.
        """
        SuiteTestCase.EVENTS.clear()
        testset = MagicMock()
        testset.paths = tuple(
            f'case{index}.py'
            for index in range(len(caseclasses))
        )
        runner = Runner(self.runner.testbed, testset)
        with patch.object(
            runner,
            '_import_case',
            side_effect=caseclasses
        ):
            with patch.object(
                runner,
                '_make_logroot',
                return_value=self.logroot
            ):
                with patch('xbot.framework.runner.enable_console_logging'):
                    with patch('xbot.framework.runner.xprint'):
                        runner.run('verbose')
        return SuiteTestCase.EVENTS.copy()

    def get_case_result_from_logfile(self, logfile: str):
        """
        Get the result of a testcase from its log file.

        :param logfile: The path of the log file.
        """
        with open(logfile, 'r', encoding='utf8') as f:
            m = re.search(rf'<td id="result" colspan="2">(.+)</td>', f.read())
            return m.group(1)

    def test_suite_chain(self) -> None:
        """
        Test suite extraction from a testcase MRO.

        :return: None.
        """
        class BaseCase(TestCase):
            pass

        class TC(BaseCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Set up the suite.

                :param testbed: TestBed instance.
                :return: None.
                """
                pass

        class TC_HGDB(TC):
            pass

        class TC_HGDB_ACCESS(TC_HGDB):
            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Tear down the suite.

                :param testbed: TestBed instance.
                :return: None.
                """
                pass

        class TC_HGDB_ACCESS_001(TC_HGDB_ACCESS):
            pass

        self.assertEqual(
            self.runner._suite_chain(TC_HGDB_ACCESS_001),
            (TC, TC_HGDB_ACCESS)
        )

    def test_suite_lifecycle_order(self) -> None:
        """
        Test nested and sibling suite lifecycle order.

        :return: None.
        """
        events = []

        class BaseCase(TestCase):
            SKIPPED = False

            def __init__(
                self,
                testbed: TestBed,
                testset: TestSet,
                logroot: str
            ) -> None:
                """
                Initialize a fake testcase.

                :param testbed: TestBed instance.
                :param testset: TestSet instance.
                :param logroot: Testcase log root.
                :return: None.
                """
                self._caseid = self.__class__.__name__

            @property
            def caseid(self) -> str:
                """
                Return the fake testcase id.

                :return: Testcase id.
                """
                return self._caseid

            @property
            def skipped(self) -> bool:
                """
                Return whether the testcase is skipped.

                :return: Skip state.
                """
                return self.SKIPPED

            def run(self, skip_reason: str | None = None) -> None:
                """
                Record testcase execution.

                :param skip_reason: External skip reason.
                :return: None.
                """
                events.append(
                    f'{self.caseid}.skip'
                    if skip_reason
                    else self.caseid
                )

        class TC(BaseCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC.teardown')

        class TC_LEFT(TC):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC_LEFT.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC_LEFT.teardown')

        class TC_LEFT_001(TC_LEFT):
            pass

        class TC_LEFT_002(TC_LEFT):
            pass

        class TC_RIGHT(TC):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC_RIGHT.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC_RIGHT.teardown')

        class TC_RIGHT_001(TC_RIGHT):
            pass

        testset = MagicMock()
        testset.paths = ('left1.py', 'left2.py', 'right1.py')
        runner = Runner(self.runner.testbed, testset)
        with patch.object(
            runner,
            '_import_case',
            side_effect=(TC_LEFT_001, TC_LEFT_002, TC_RIGHT_001)
        ):
            with patch.object(
                runner,
                '_make_logroot',
                return_value=self.logroot
            ):
                with patch('xbot.framework.runner.enable_console_logging'):
                    with patch('xbot.framework.runner.xprint'):
                        runner.run('verbose')

        self.assertEqual(events, [
            'TC.setup',
            'TC_LEFT.setup',
            'TC_LEFT_001',
            'TC_LEFT_002',
            'TC_LEFT.teardown',
            'TC_RIGHT.setup',
            'TC_RIGHT_001',
            'TC_RIGHT.teardown',
            'TC.teardown'
        ])

    def test_suite_setup_failure(self) -> None:
        """
        Test setup failure isolation and sibling execution.

        :return: None.
        """
        class TC(SuiteTestCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC.teardown')

        class TC_LEFT(TC):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Fail suite setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_LEFT.setup')
                raise RuntimeError('setup failed')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_LEFT.teardown')

        class TC_LEFT_CHILD(TC_LEFT):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_LEFT_CHILD.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_LEFT_CHILD.teardown')

        class TC_LEFT_CHILD_001(TC_LEFT_CHILD):
            pass

        class TC_LEFT_CHILD_002(TC_LEFT_CHILD):
            pass

        class TC_RIGHT(TC):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_RIGHT.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_RIGHT.teardown')

        class TC_RIGHT_001(TC_RIGHT):
            pass

        events = self.run_suite_cases(
            TC_LEFT_CHILD_001,
            TC_LEFT_CHILD_002,
            TC_RIGHT_001
        )
        self.assertEqual(events, [
            'TC.setup',
            'TC_LEFT.setup',
            'TC_LEFT_CHILD_001.skip:Suite TC_LEFT setup failed.',
            'TC_LEFT_CHILD_002.skip:Suite TC_LEFT setup failed.',
            'TC_LEFT.teardown',
            'TC_RIGHT.setup',
            'TC_RIGHT_001',
            'TC_RIGHT.teardown',
            'TC.teardown'
        ])

    def test_suite_teardown_failure(self) -> None:
        """
        Test that teardown failure does not block parent cleanup.

        :return: None.
        """
        class TC(SuiteTestCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC.teardown')

        class TC_CHILD(TC):
            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Fail suite teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_CHILD.teardown')
                raise RuntimeError('teardown failed')

        class TC_CHILD_001(TC_CHILD):
            pass

        events = self.run_suite_cases(TC_CHILD_001)
        self.assertEqual(events[-2:], [
            'TC_CHILD.teardown',
            'TC.teardown'
        ])

    def test_all_suite_cases_filtered(self) -> None:
        """
        Test that a fully filtered suite runs no hooks.

        :return: None.
        """
        class TC_FILTERED(SuiteTestCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_FILTERED.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_FILTERED.teardown')

        class TC_FILTERED_001(TC_FILTERED):
            SKIPPED = True

        events = self.run_suite_cases(TC_FILTERED_001)
        self.assertEqual(events, ['TC_FILTERED_001'])

    def test_some_suite_cases_filtered(self) -> None:
        """
        Test that filtering one case keeps its suite active.

        :return: None.
        """
        class TC_PARTIAL(SuiteTestCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_PARTIAL.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_PARTIAL.teardown')

        class TC_PARTIAL_001(TC_PARTIAL):
            pass

        class TC_PARTIAL_002(TC_PARTIAL):
            SKIPPED = True

        class TC_PARTIAL_003(TC_PARTIAL):
            pass

        events = self.run_suite_cases(
            TC_PARTIAL_001,
            TC_PARTIAL_002,
            TC_PARTIAL_003
        )
        self.assertEqual(events, [
            'TC_PARTIAL.setup',
            'TC_PARTIAL_001',
            'TC_PARTIAL_002',
            'TC_PARTIAL_003',
            'TC_PARTIAL.teardown'
        ])

    def test_run(self):
        """
        Test `Runner.run` method.
        """
        with utils.cd(self.workdir):
            with patch('sys.stdout', new_callable=StringIO):
                with patch('sys.stderr', new_callable=StringIO):
                    logroot = self.runner.run()
        self.assertTrue(os.path.exists(logroot))
        self.assertEqual(
            self.get_case_result_from_logfile(
                os.path.join(logroot, 
                             'testcases', 
                             'examples', 
                             'nonpass', 
                             'tc_eg_nonpass_error_clsname.html')
            ), 
            'ERROR'
        )
        self.assertEqual(
            self.get_case_result_from_logfile(
                os.path.join(logroot, 
                             'testcases', 
                             'examples', 
                             'nonpass', 
                             'tc_eg_nonpass_error_syntax.html')
            ), 
            'ERROR'
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)
