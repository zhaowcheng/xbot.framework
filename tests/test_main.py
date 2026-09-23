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

    def samedir(
        self,
        dir1: str,
        dir2: str,
        ignore: list[str] | None = None
    ) -> bool:
        """
        Compare two directories recursively.

        :param dir1: first directory path.
        :param dir2: second directory path.
        :param ignore: names to ignore in the comparison.
        :return: True if the two directories are identical.
        """
        dcmp = filecmp.dircmp(dir1, dir2, ignore=ignore, hide=None)
        return (
            not dcmp.left_only and
            not dcmp.right_only and
            not dcmp.diff_files and
            all(self.samedir(
                os.path.join(dcmp.left, subdir),
                os.path.join(dcmp.right, subdir),
                ignore
            ) for subdir in dcmp.common_dirs)
        )

    def test_init(self):
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            tmpdir1 = tempfile.mktemp()
            main.init(tmpdir1)
            self.assertIn(f'Initialized {tmpdir1}', mockout.getvalue())
            self.assertTrue(self.samedir(tmpdir1, INIT_DIR, ['requirements.txt']),
                            f'{tmpdir1} is not same as {INIT_DIR}')
            major = int(__version__.split('.')[0])
            reqfile = os.path.join(tmpdir1, 'requirements.txt')
            with open(reqfile, encoding='utf8') as f:
                self.assertEqual(
                    f.read(),
                    "xbot.framework>=%d,<%d; python_version >= '3.10'\n"
                    % (major, major + 1)
                )
            with open(os.path.join(INIT_DIR, 'requirements.txt'), encoding='utf8') as f:
                self.assertEqual(f.read(), "xbot.framework; python_version >= '3.10'\n")
            shutil.rmtree(tmpdir1)
        tmpdir2 = tempfile.mkdtemp()
        mockerr = StringIO()
        utils.printerr.keywords['file'] = mockerr
        with self.assertRaises(SystemExit) as cm:
            main.init(tmpdir2)
            self.assertEqual(cm.exception.code, 1)
        self.assertIn(f'{tmpdir2} already exists', mockerr.getvalue())
        shutil.rmtree(tmpdir2)

    def test_init_with_other_deps(self):
        initdir = tempfile.mktemp()
        shutil.copytree(INIT_DIR, initdir)
        reqfile = os.path.join(initdir, 'requirements.txt')
        with open(reqfile, 'w', encoding='utf8') as f:
            f.write("jinja2\nxbot.framework; python_version >= '3.10'\njmespath\n")
        tmpdir = tempfile.mktemp()
        try:
            with patch('sys.stdout', new_callable=StringIO):
                with patch('xbot.framework.main.INIT_DIR', initdir):
                    main.init(tmpdir)
            major = int(__version__.split('.')[0])
            with open(os.path.join(tmpdir, 'requirements.txt'), encoding='utf8') as f:
                self.assertEqual(
                    f.read(),
                    "jinja2\nxbot.framework>=%d,<%d; python_version >= '3.10'\n"
                    "jmespath\n" % (major, major + 1)
                )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            shutil.rmtree(initdir, ignore_errors=True)
        
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
