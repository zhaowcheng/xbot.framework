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
    @classmethod
    def setUpClass(cls) -> None:
        cls.workdir = tempfile.mktemp()
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
