import unittest
import doctest
import socket
import threading
import time
import sys
import os
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from io import StringIO
from unittest.mock import patch

from xbot.framework import utils


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


class TestUtils(unittest.TestCase):
    """
    Unit tests for utils module.
    """
    def test_stop_thread(self):
        """
        Test `stop_thread` function.
        """
        def func():
            while True:
                time.sleep(0.1)
        thread = threading.Thread(target=func)
        thread.start()
        utils.stop_thread(thread)
        time.sleep(0.2)
        self.assertFalse(thread.is_alive())

    def test_xprint_without_color(self):
        """
        Test `xprint` without color.
        """
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            s = 'Hello World!'
            utils.xprint(s, file=sys.stdout)
            self.assertEqual(mockout.getvalue().strip(), s)

    def test_xprint_with_color(self):
        """
        Test `xprint` with color.
        """
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            s = 'Hello World!'
            utils.xprint(s, color='green', file=sys.stdout)
            self.assertEqual(mockout.getvalue().strip(), 
                             utils.ColorText.wrap(s, 'green'))
            
    def test_xprint_with_exit(self):
        """
        Test `xprint` with exit.
        """
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            with self.assertRaises(SystemExit) as cm:
                utils.xprint('Exit Message', file=sys.stdout, 
                             do_exit=True, exit_code=99)
                self.assertEqual(cm.exception.code, 99)

    def test_printerr(self):
        """
        Test `printerr` function.
        """
        with patch('sys.stderr', new_callable=StringIO) as mockerr:
            with self.assertRaises(SystemExit) as cm:
                s = 'Error Message'
                utils.printerr(s, file=sys.stderr)
                self.assertEqual(cm.exception.code, 1)
                self.assertEqual(mockerr.getvalue().strip(), 
                                 utils.ColorText.wrap(s, 'red'))
                
    def test_cd(self):
        """
        Test `cd` context manager.
        """
        cwd = os.getcwd()
        parent = os.path.dirname(cwd)
        with utils.cd(parent):
            self.assertEqual(os.getcwd(), parent)
        self.assertEqual(os.getcwd(), cwd)


if __name__ == '__main__':
    unittest.main(verbosity=2)
