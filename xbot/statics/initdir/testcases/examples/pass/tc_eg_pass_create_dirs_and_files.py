import os
import tempfile
import shutil

from xbot.utils import assertx

from lib.testcase import TestCase


class tc_eg_pass_create_dirs_and_files(TestCase):
    """
    测试创建目录和文件。
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1']

    def setup(self):
        """
        创建一个临时工作目录。
        """
        self.workdir = tempfile.mkdtemp()
        self.info('Created workdir: %s', self.workdir)

    def step1(self):
        """
        在临时工作目录下下创建子目录 `dir`，并检查是否创建成功。
        """
        self.dir1 = os.path.join(self.workdir, 'dir1')
        os.mkdir(self.dir1)
        assertx(os.path.exists(self.dir1), '==', True)

    def step2(self):
        """
        在 `dir1` 下创建空文件 `file1`，并检查是否创建成功。
        """
        self.file1 = os.path.join(self.dir1, 'file1')
        open(self.file1, 'w').close()
        assertx(os.path.exists(self.file1), '==', True)

    def step3(self):
        """
        写入 `hello world` 到 `file1` 中，并检查是否写入成功。
        """
        with open(self.file1, 'w') as f:
            f.write('hello world')
        with open(self.file1, 'r') as f:
            assertx(f.read(), '==', 'hello world')

    def teardown(self):
        """
        删除临时工作目录。
        """
        shutil.rmtree(self.workdir)
        self.info('Removed workdir: %s', self.workdir)
        self.sleep(1)
