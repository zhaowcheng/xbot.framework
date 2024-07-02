import os
import re
import sys
import unittest
import tempfile
import shutil
import filecmp
import logging

from io import StringIO
from unittest.mock import patch, MagicMock

from xbot.framework import main, utils
from xbot.framework.common import INIT_DIR
from xbot.framework.logger import ROOT_LOGGER
from xbot.framework.version import __version__


class TestMain(unittest.TestCase):
    """
    Unit tests for main module.
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.workdir = tempfile.mktemp()
        shutil.copytree(INIT_DIR, cls.workdir)
        # Hide console output.
        for hdlr in ROOT_LOGGER.handlers:
            if isinstance(hdlr, logging.StreamHandler) \
                    and hdlr.stream in [sys.stdout, sys.stderr]:
                hdlr.stream = StringIO()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.workdir)

    def samedir(self, dir1: str, dir2: str) -> bool:
        """
        Compare two directories recursively.
        """
        dcmp = filecmp.dircmp(dir1, dir2, ignore=None, hide=None)
        return (
            not dcmp.left_only and
            not dcmp.right_only and
            not dcmp.diff_files and
            all(self.samedir(
                os.path.join(dcmp.left, subdir),
                os.path.join(dcmp.right, subdir)
            ) for subdir in dcmp.common_dirs)
        )

    def test_init(self):
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            tmpdir1 = tempfile.mktemp()
            main.init(tmpdir1)
            self.assertIn(f'Initialized {tmpdir1}', mockout.getvalue())
            self.assertTrue(self.samedir(tmpdir1, INIT_DIR), 
                            f'{tmpdir1} is not same as {INIT_DIR}')
            shutil.rmtree(tmpdir1)
        tmpdir2 = tempfile.mkdtemp()
        mockerr = StringIO()
        utils.printerr.keywords['file'] = mockerr
        with self.assertRaises(SystemExit) as cm:
            main.init(tmpdir2)
            self.assertEqual(cm.exception.code, 1)
        self.assertIn(f'{tmpdir2} already exists', mockerr.getvalue())
        shutil.rmtree(tmpdir2)
        
    def test_is_projdir(self):
        self.assertTrue(main.is_projdir(self.workdir))
        self.assertFalse(main.is_projdir(os.path.dirname(self.workdir)))

    def test_run(self):
        mockerr = StringIO()
        utils.printerr.keywords['file'] = mockerr
        with self.assertRaises(SystemExit) as cm:
            main.run('testbeds/testbed_example.yml', 
                     'testsets/testset_example.yml')
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('No `testcases`', mockerr.getvalue())
        with utils.cd(self.workdir):
            with patch('sys.stdout', new_callable=StringIO) as mockout:
                with self.assertRaises(SystemExit) as cm:
                    main.run('testbeds/testbed_example.yml', 
                            'testsets/testset_example.yml')
                    self.assertEqual(cm.exception.code, 1)
                    self.assertIn('Generating report...', mockout.getvalue())
                    report = re.search(r'Generating report...\s+(\S+report.html)', 
                                    mockout.getvalue()).group(1)
                    self.assertTrue(os.path.exists(report))

    def test_main(self):
        with patch('xbot.framework.main.init', new_callable=MagicMock) as mockinit:
            sys.argv = ['xbot', 'init', '-d', 'myproj']
            main.main()
            mockinit.assert_called_once_with('myproj')
        with patch('xbot.framework.main.run', new_callable=MagicMock) as mockrun:
            sys.argv = ['xbot', 'run', '-b', 'mytb.yml', '-s', 'myts.yml']
            main.main()
            mockrun.assert_called_once_with('mytb.yml', 'myts.yml', 'brief')
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            sys.argv = ['xbot', '-v']
            with self.assertRaises(SystemExit) as cm:
                main.main()
                self.assertEqual(cm.exception.code, 0)
                self.assertIn(f'xbot {__version__}', mockout.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
