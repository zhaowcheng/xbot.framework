import os
import unittest

from xbot.framework.report import gen_report


LOGDIR = os.path.join(os.path.dirname(__file__), 'resources', 'logs')
OKREPORT = os.path.join(LOGDIR, 'report.ok.html')


class TestReport(unittest.TestCase):
    """
    Unit tests for report module.
    """
    def test_gen_report(self):
        """
        Test `gen_report` function.
        """
        report, _ = gen_report(LOGDIR)
        with open(report, encoding='utf8') as f1:
            with open(OKREPORT, encoding='utf8') as f2:
                content = f1.read()
                self.assertEqual(content, f2.read(),
                                 f'{report} != {OKREPORT}')
        self.assertIn('var superCasesVisible = true;', content)
        self.assertIn('var currentFilterLevel = 0;', content)
        self.assertIn("id='super_toggle'", content)
        self.assertIn('HIDE SUPER SETUPS/TEARDOWNS', content)
        self.assertIn('SHOW SUPER SETUPS/TEARDOWNS', content)
        self.assertIn(
            "tr.style.display = superCasesVisible ? null : 'none';",
            content
        )
        self.assertIn('filterCase(currentFilterLevel);', content)
        os.remove(report)


if __name__ == '__main__':
    unittest.main(verbosity=2)
