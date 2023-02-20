# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

import unittest
import shutil
import os
import sys
sys.path.append(os.path.abspath(f'{__file__}/../..'))

from lib.sftp import SFTP


class TestSFTP(unittest.TestCase):

    HOST = ''
    PORT = 22
    USER = ''
    PWD = ''

    sftp = SFTP()

    LHOME = os.environ.get('HOME') or os.environ['HOMEPATH']
    LPUTDIR = os.path.join(LHOME, 'lputdir')
    LGETDIR = os.path.join(LHOME, 'lgetdir')
    RPUTDIR = '/tmp/rputgetdir'
    RGETDIR = RPUTDIR

    @classmethod
    def setUpClass(cls):
        cls.sftp.connect(cls.HOST, cls.USER, 
                         cls.PWD, cls.PORT)
        if not cls.sftp.exists(cls.RPUTDIR):
            cls.sftp.makedirs(cls.RPUTDIR)
        os.makedirs(os.path.join(cls.LPUTDIR, 'dir', 'subdir'))
        os.system('whoami > %s' % os.path.join(cls.LPUTDIR, 'file'))
        os.system('whoami > %s' % os.path.join(cls.LPUTDIR, 'dir', 'subfile'))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.LPUTDIR)
        shutil.rmtree(cls.LGETDIR)
        cls.sftp.close()

    def test_01_putdir(self):
        l = os.path.join(self.LPUTDIR, 'dir')
        self.sftp.putdir(l, self.RPUTDIR)
        p1 = self.sftp.join(self.RPUTDIR, 'dir', 'subdir')
        self.assertTrue(self.sftp.exists(p1))
        p2 = self.sftp.join(self.RPUTDIR, 'dir', 'subfile')
        self.assertTrue(self.sftp.exists(p2))

    def test_02_putfile(self):
        l = os.path.join(self.LPUTDIR, 'file')
        self.sftp.putfile(l, self.RPUTDIR)
        p = self.sftp.join(self.RPUTDIR, 'file')
        self.assertTrue(self.sftp.exists(p))

    def test_03_getdir(self):
        r = self.sftp.join(self.RGETDIR, 'dir')
        self.sftp.getdir(r, self.LGETDIR)
        p1 = os.path.join(self.LGETDIR, 'dir', 'subdir')
        self.assertTrue(os.path.exists(p1))
        p2 = os.path.join(self.LGETDIR, 'dir', 'subfile')
        self.assertTrue(os.path.exists(p2))
    
    def test_04_getfile(self):
        r = self.sftp.join(self.RGETDIR, 'file')
        self.sftp.getfile(r, self.LGETDIR)
        p = os.path.join(self.LGETDIR, 'file')
        self.assertTrue(os.path.exists(p))

    def test_05_open(self):
        p = self.sftp.join(self.RPUTDIR, 'file')
        with self.sftp.open(p, 'a') as fp:
            fp.write('xbot\n')
        with self.sftp.open(p, 'r') as fp:
            self.assertIn('xbot', fp.read().decode('utf-8'))


if __name__ == '__main__':
    test = unittest.TestLoader().loadTestsFromTestCase(TestSFTP) 
    unittest.TextTestRunner(verbosity=2).run(test)