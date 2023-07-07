# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>


import unittest
import shutil
import sys
import os
import invoke
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from lib.ssh import SSH
from lib.error import ShellError


class TestSSH(unittest.TestCase):

    HOST = ''
    PORT = 22
    USER = ''
    PWD = ''

    LHOME = os.environ.get('HOME') or os.environ['HOMEPATH']
    LPUTDIR = os.path.join(LHOME, 'lputdir')
    LGETDIR = os.path.join(LHOME, 'lgetdir')
    RPUTDIR = '/tmp/rputgetdir'
    RGETDIR = RPUTDIR

    ssh = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.ssh = SSH(cls.HOST, cls.USER, cls.PWD, cls.PORT)
        if not cls.ssh.exists(cls.RPUTDIR):
            cls.ssh.makedirs(cls.RPUTDIR)
        os.makedirs(os.path.join(cls.LPUTDIR, 'dir', 'subdir'))
        os.system('whoami > %s' % os.path.join(cls.LPUTDIR, 'file'))
        os.system('whoami > %s' % os.path.join(cls.LPUTDIR, 'dir', 'subfile'))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.LPUTDIR)
        shutil.rmtree(cls.LGETDIR)
        cls.ssh.close()

    def test_cmd_whoami(self):
        self.assertEqual(self.ssh.exec('whoami'), self.USER)

    def test_cmd_interact(self):
        self.ssh.exec("read -p 'input: '", prompts={'input:': 'hello'})

    def test_cmd_timeout(self):
        with self.assertRaises(invoke.exceptions.CommandTimedOut):
            self.ssh.exec('sleep 3', timeout=2)

    def test_cmd_cd(self):
        with self.ssh.cd('/tmp'):
            self.assertEqual(self.ssh.exec('pwd'), '/tmp')
    
    def test_cmd_sudo(self):
        self.assertEqual(self.ssh.sudo('whoami'), 'root')

    def test_sftp_01_putdir(self):
        l = os.path.join(self.LPUTDIR, 'dir')
        self.ssh.putdir(l, self.RPUTDIR)
        p1 = self.ssh.join(self.RPUTDIR, 'dir', 'subdir')
        self.assertTrue(self.ssh.exists(p1))
        p2 = self.ssh.join(self.RPUTDIR, 'dir', 'subfile')
        self.assertTrue(self.ssh.exists(p2))

    def test_sftp_02_putfile(self):
        l = os.path.join(self.LPUTDIR, 'file')
        self.ssh.putfile(l, self.RPUTDIR)
        p = self.ssh.join(self.RPUTDIR, 'file')
        self.assertTrue(self.ssh.exists(p))

    def test_sftp_03_getdir(self):
        r = self.ssh.join(self.RGETDIR, 'dir')
        self.ssh.getdir(r, self.LGETDIR)
        p1 = os.path.join(self.LGETDIR, 'dir', 'subdir')
        self.assertTrue(os.path.exists(p1))
        p2 = os.path.join(self.LGETDIR, 'dir', 'subfile')
        self.assertTrue(os.path.exists(p2))
    
    def test_sftp_04_getfile(self):
        r = self.ssh.join(self.RGETDIR, 'file')
        self.ssh.getfile(r, self.LGETDIR)
        p = os.path.join(self.LGETDIR, 'file')
        self.assertTrue(os.path.exists(p))

    def test_sftp_05_openfile(self):
        p = self.ssh.join(self.RPUTDIR, 'file')
        with self.ssh.openfile(p, 'a') as fp:
            fp.write('xbot\n')
        with self.ssh.openfile(p, 'r') as fp:
            self.assertIn('xbot', fp.read().decode('utf-8'))
    


if __name__ == '__main__':
    test = unittest.TestLoader().loadTestsFromTestCase(TestSSH)
    unittest.TextTestRunner(verbosity=2).run(test)
