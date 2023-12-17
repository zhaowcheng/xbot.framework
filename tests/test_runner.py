import os
import sys
import re
import unittest
import tempfile
import shutil

from io import StringIO

from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.runner import Runner
from xbot.common import INIT_DIR

sys.path.append(INIT_DIR)

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

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.workdir)

    def get_case_result_from_logfile(self, logfile: str):
        """
        从用例日志中获取测试用例的执行结果。

        :param logfile: 用例日志路径。
        """
        with open(logfile, 'r') as f:
            m = re.search(rf'<td id="result" colspan="2">(.+)</td>', f.read())
            return m.group(1)

    def test_run(self):
        """
        测试 run 函数。
        """
        os.chdir(self.workdir)
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
