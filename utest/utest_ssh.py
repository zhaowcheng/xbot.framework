# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

import unittest
import shutil
import sys
import os
import invoke
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from lib.ssh import SSH


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

    conn = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.conn = SSH(cls.HOST, cls.USER, cls.PWD, cls.PORT)
        if not cls.conn.exists(cls.RPUTDIR):
            cls.conn.makedirs(cls.RPUTDIR)
        os.makedirs(os.path.join(cls.LPUTDIR, 'dir', 'subdir'))
        os.system('whoami > %s' % os.path.join(cls.LPUTDIR, 'file'))
        os.system('whoami > %s' % os.path.join(cls.LPUTDIR, 'dir', 'subfile'))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.LPUTDIR)
        shutil.rmtree(cls.LGETDIR)
        cls.conn.close()

    def test_cmd_whoami(self):
        self.assertEqual(self.conn.exec('whoami'), self.USER)

    def test_cmd_interact(self):
        self.conn.exec("read -p 'input: '", prompts={'input:': 'hello'})

    def test_cmd_timeout(self):
        with self.assertRaises(invoke.exceptions.CommandTimedOut):
            self.conn.exec('sleep 3', timeout=2)

    def test_cmd_cd(self):
        with self.conn.cd('/tmp'):
            self.assertEqual(self.conn.exec('pwd'), '/tmp')
    
    def test_cmd_sudo(self):
        self.assertEqual(self.conn.sudo('whoami'), 'root')

    def test_sftp_01_putdir(self):
        l = os.path.join(self.LPUTDIR, 'dir')
        self.conn.putdir(l, self.RPUTDIR)
        p1 = self.conn.join(self.RPUTDIR, 'dir', 'subdir')
        self.assertTrue(self.conn.exists(p1))
        p2 = self.conn.join(self.RPUTDIR, 'dir', 'subfile')
        self.assertTrue(self.conn.exists(p2))

    def test_sftp_02_putfile(self):
        l = os.path.join(self.LPUTDIR, 'file')
        self.conn.putfile(l, self.RPUTDIR)
        p = self.conn.join(self.RPUTDIR, 'file')
        self.assertTrue(self.conn.exists(p))

    def test_sftp_03_getdir(self):
        r = self.conn.join(self.RGETDIR, 'dir')
        self.conn.getdir(r, self.LGETDIR)
        p1 = os.path.join(self.LGETDIR, 'dir', 'subdir')
        self.assertTrue(os.path.exists(p1))
        p2 = os.path.join(self.LGETDIR, 'dir', 'subfile')
        self.assertTrue(os.path.exists(p2))
    
    def test_sftp_04_getfile(self):
        r = self.conn.join(self.RGETDIR, 'file')
        self.conn.getfile(r, self.LGETDIR)
        p = os.path.join(self.LGETDIR, 'file')
        self.assertTrue(os.path.exists(p))

    def test_sftp_05_openfile(self):
        p = self.conn.join(self.RPUTDIR, 'file')
        with self.conn.openfile(p, 'a') as fp:
            fp.write('xbot\n')
        with self.conn.openfile(p, 'r') as fp:
            self.assertIn('xbot', fp.read().decode('utf-8'))


if __name__ == '__main__':
    test = unittest.TestLoader().loadTestsFromTestCase(TestSSH)
    unittest.TextTestRunner(verbosity=2).run(test)
