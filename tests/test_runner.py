import os
import sys
import re
import unittest
import tempfile
import shutil
import logging

from io import StringIO
from unittest.mock import patch

from xbot.framework import utils
from xbot.framework.testbed import TestBed
from xbot.framework.testset import TestSet
from xbot.framework.runner import Runner
from xbot.framework.common import INIT_DIR
from xbot.framework.logger import ROOT_LOGGER


class TestRunner(unittest.TestCase):
    """
    Unit tests for runner module.
    """
    @staticmethod
    def _clear_project_modules() -> None:
        """
        Remove modules imported from copied example projects.

        :return: None.
        """
        for name in tuple(sys.modules):
            if name == 'lib' or name.startswith('lib.') \
                    or name == 'testcases' \
                    or name.startswith('testcases.'):
                del sys.modules[name]

    @classmethod
    def setUpClass(cls) -> None:
        cls.workdir = tempfile.mktemp()
        shutil.copytree(INIT_DIR, cls.workdir)
        cls._clear_project_modules()
        sys.path.insert(0, cls.workdir)
        # Hide console output.
        for hdlr in ROOT_LOGGER.handlers:
            if isinstance(hdlr, logging.StreamHandler) \
                    and hdlr.stream in [sys.stdout, sys.stderr]:
                hdlr.stream = StringIO()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._clear_project_modules()
        sys.path.remove(cls.workdir)
        shutil.rmtree(cls.workdir)

    def tearDown(self) -> None:
        """
        Remove logs created by one test.

        :return: None.
        """
        logdir = os.path.join(self.workdir, 'logs')
        if os.path.exists(logdir):
            shutil.rmtree(logdir)

    def run_testset(self, filename: str) -> tuple[str, str]:
        """
        Run a testset from the copied example project.

        :param filename: Testset filename.
        :return: Log root and captured stdout.
        """
        with utils.cd(self.workdir):
            runner = Runner(
                TestBed(
                    os.path.join(
                        self.workdir,
                        'testbeds',
                        'testbed_example.yml',
                    ),
                ),
                TestSet(os.path.join(self.workdir, 'testsets', filename)),
            )
            with patch('sys.stdout', new_callable=StringIO) as stdout:
                with patch('sys.stderr', new_callable=StringIO):
                    logroot = runner.run()
        return logroot, stdout.getvalue()

    def get_case_result_from_logfile(self, logfile: str):
        """
        Get the result of a testcase from its log file.

        :param logfile: The path of the log file.
        """
        with open(logfile, 'r', encoding='utf8') as f:
            m = re.search(rf'<td id="result" colspan="2">(.+)</td>', f.read())
            return m.group(1)

    def test_run(self):
        """
        Test `Runner.run` method.
        """
        logroot, _ = self.run_testset('testset_example.yml')
        self.assertTrue(os.path.exists(logroot))
        self.assertEqual(
            self.get_case_result_from_logfile(
                os.path.join(
                    logroot,
                    'testcases',
                    'examples',
                    'inst',
                    'tc_eg_install_the_software_to_be_tested_successful.html',
                ),
            ),
            'PASS',
        )
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

    def test_failed_install_interrupts_execution(self):
        """
        Stop remaining install and test cases after an install failure.
        """
        filename = 'testset_install_failed.yml'
        filepath = os.path.join(self.workdir, 'testsets', filename)
        with open(filepath, 'w', encoding='utf8') as testset_file:
            testset_file.write(
                """
tags:
  include:
    - tag1
  exclude:
testcases:
  install:
    - testcases/examples/inst/tc_eg_install_the_software_to_be_tested_failed.py
    - testcases/examples/inst/tc_eg_install_the_software_to_be_tested_successful.py
  test:
    - testcases/examples/pass/tc_eg_pass_get_values_from_testbed.py
""",
            )

        logroot, output = self.run_testset(filename)
        failed = os.path.join(
            logroot,
            'testcases',
            'examples',
            'inst',
            'tc_eg_install_the_software_to_be_tested_failed.html',
        )
        successful = os.path.join(
            logroot,
            'testcases',
            'examples',
            'inst',
            'tc_eg_install_the_software_to_be_tested_successful.html',
        )
        tested = os.path.join(
            logroot,
            'testcases',
            'examples',
            'pass',
            'tc_eg_pass_get_values_from_testbed.html',
        )

        self.assertEqual(self.get_case_result_from_logfile(failed), 'FAIL')
        self.assertFalse(os.path.exists(successful))
        self.assertFalse(os.path.exists(tested))
        self.assertIn('Execution was interrupted', output)

if __name__ == '__main__':
    unittest.main(verbosity=2)
