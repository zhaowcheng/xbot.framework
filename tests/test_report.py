import os
import unittest

from xbot.report import gen_report


LOGDIR = os.path.join(os.path.dirname(__file__), 'resources', 'logs')
OKREPORT = os.path.join(LOGDIR, 'report.ok.html')


class TestReport(unittest.TestCase):
    """
    report 模块单元测试。
    """
    def test_gen_report(self):
        """
        测试 gen_report 函数。
        """
        report, _ = gen_report(LOGDIR)
        with open(report) as f1:
            with open(OKREPORT) as f2:
                self.assertEqual(f1.read(), f2.read())
        os.remove(report)


if __name__ == '__main__':
    unittest.main(verbosity=2)
