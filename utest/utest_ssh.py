# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>


import unittest
import threading
import sys
import os
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from lib.ssh import SSH
from lib.error import ShellError


class TestSSH(unittest.TestCase):

    HOST = ''
    PORT = 22
    USER = ''
    PWD = ''

    ssh = SSH()

    def setenv(self, name: str, value: str) -> None:
        self.ssh.exec(f'export {name}="{value}"')

    def getenv(self, name: str) -> str:
        return self.ssh.exec(f'echo ${name}')

    @classmethod
    def setUpClass(cls) -> None:
        cls.ssh.connect(cls.HOST, cls.USER, cls.PWD, cls.PORT)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ssh.close()

    def test_cmd_whoami(self):
        self.ssh.exec('whoami', expect=self.USER)

    def test_cmd_interact(self):
        self.ssh.exec("read -p 'input: '", expect='input:')
        self.ssh.exec('hello')

    def test_expect_0(self):
        self.ssh.exec('cd /home', expect='0')
        with self.assertRaises(ShellError):
            self.ssh.exec('cd /errpath', expect='0')

    def test_expect_null(self):
        self.ssh.exec('cd /home', expect='')
        self.ssh.exec('cd /errpath', expect='')

    def test_timeout(self):
        with self.assertRaises(ShellError):
            self.ssh.exec('sleep 5', timeout=3)

    def test_thread_safe(self):
        def _setenv(name, value):
            self.setenv(name, value)
            rs = self.getenv(name)
            self.assertEqual(rs, value)
        t1 = threading.Thread(target=_setenv, args=('XBOT', 't1'))
        t2 = threading.Thread(target=_setenv, args=('XBOT', 't2'))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    def test_preset_shenvs(self):
        shenvs = {'XBOT_HOME': '/home/xbot'}
        ssh = SSH(shenvs=shenvs)
        ssh.connect(self.HOST, self.USER, self.PWD, self.PORT)
        rs = ssh.exec('echo $XBOT_HOME')
        self.assertEqual(rs, '/home/xbot')
        ssh.close()


if __name__ == '__main__':
    test = unittest.TestLoader().loadTestsFromTestCase(TestSSH)
    unittest.TextTestRunner(verbosity=2).run(test)
