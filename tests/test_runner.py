import os
import sys
import re
import unittest
import tempfile
import shutil
import logging

from io import StringIO
from unittest.mock import patch

from xbot import utils
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.runner import Runner
from xbot.common import INIT_DIR
from xbot.logger import ROOT_LOGGER


class TestRunner(unittest.TestCase):
    """
    测试 runner 模块。
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.workdir = tempfile.mktemp()
        shutil.copytree(INIT_DIR, cls.workdir)
        cls.runner = Runner(
            TestBed(os.path.join(cls.workdir, 'testbeds', 'testbed_example.yml')),
            TestSet(os.path.join(cls.workdir, 'testsets', 'testset_example.yml'))
        )
        # 将用例执行时的控制台日志重定向到 StringIO
        for hdlr in ROOT_LOGGER.handlers:
            if isinstance(hdlr, logging.StreamHandler) \
                    and hdlr.stream in [sys.stdout, sys.stderr]:
                hdlr.stream = StringIO()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.workdir)

    def get_case_result_from_logfile(self, logfile: str):
        """
        从用例日志中获取测试用例的执行结果。

        :param logfile: 用例日志路径。
        """
        with open(logfile, 'r', encoding='utf8') as f:
            m = re.search(rf'<td id="result" colspan="2">(.+)</td>', f.read())
            return m.group(1)

    def test_run(self):
        """
        测试 run 函数。
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
