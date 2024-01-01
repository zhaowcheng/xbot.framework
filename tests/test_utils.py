import unittest
import doctest
import socket
import threading
import tempfile
import time
import sys
import os
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from io import StringIO
from unittest.mock import patch

from xbot import utils


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


class TestUtils(unittest.TestCase):
    """
    utils 模块单元测试。
    """
    def get_first_busy_or_idle_port(
            self, 
            ip: str,
            start: int, 
            end: int,
            typ: str
        ) -> int:
        """
        获取主机第一个占用或空闲的端口。
        """
        for port in range(start, end):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.1)
                result = sock.connect_ex((ip, port))
                if typ == 'busy' and result == 0:
                    return port
                elif typ == 'idle' and result != 0:
                    return port

    def test_port_opened(self):
        """
        测试 port_opened 函数。
        """
        busyport = self.get_first_busy_or_idle_port('127.0.0.1', 1, 65535, 'busy')
        idleport = self.get_first_busy_or_idle_port('127.0.0.1', 1, 65535, 'idle')
        self.assertTrue(utils.port_opened('127.0.0.1', busyport))
        self.assertFalse(utils.port_opened('127.0.0.1', idleport))

    def test_stop_thread(self):
        """
        测试 stop_thread 函数。
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
        测试 xprint 不带颜色。
        """
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            s = 'Hello World!'
            utils.xprint(s, file=sys.stdout)
            self.assertEqual(mockout.getvalue().strip(), s)

    def test_xprint_with_color(self):
        """
        测试 xprint 带颜色。
        """
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            s = 'Hello World!'
            utils.xprint(s, color='green', file=sys.stdout)
            self.assertEqual(mockout.getvalue().strip(), 
                             utils.ColorText.wrap(s, 'green'))
            
    def test_xprint_with_exit(self):
        """
        测试 xprint 后退出。
        """
        with patch('sys.stdout', new_callable=StringIO) as mockout:
            with self.assertRaises(SystemExit) as cm:
                utils.xprint('Exit Message', file=sys.stdout, 
                             do_exit=True, exit_code=99)
                self.assertEqual(cm.exception.code, 99)

    def test_printerr(self):
        """
        测试 printerr 函数。
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
        测试 cd 函数。
        """
        cwd = os.getcwd()
        parent = os.path.dirname(cwd)
        with utils.cd(parent):
            self.assertEqual(os.getcwd(), parent)
        self.assertEqual(os.getcwd(), cwd)


if __name__ == '__main__':
    unittest.main(verbosity=2)
