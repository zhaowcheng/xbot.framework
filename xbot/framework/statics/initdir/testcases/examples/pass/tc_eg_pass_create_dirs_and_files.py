import os
import tempfile
import shutil

from xbot.framework.utils import assertx
from lib.testcase import TestCase


class tc_eg_pass_create_dirs_and_files(TestCase):
    """
    Test creating directories and files.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare test environment.
        """
        self.workdir = tempfile.mkdtemp()
        self.info('Created workdir: %s', self.workdir)

    def step1(self):
        """
        Create a subdirectory 'dir' under the temporary working directory and check if it is created successfully.
        """
        self.dir1 = os.path.join(self.workdir, 'dir1')
        os.mkdir(self.dir1)
        assertx(os.path.exists(self.dir1), '==', True)

    def step2(self):
        """
        Create an empty file 'file1' under 'dir1' and check if it is created successfully.
        """
        self.file1 = os.path.join(self.dir1, 'file1')
        open(self.file1, 'w').close()
        assertx(os.path.exists(self.file1), '==', True)

    def step3(self):
        """
        Write 'hello world' to 'file1' and check if it is written successfully.
        """
        with open(self.file1, 'w') as f:
            f.write('hello world')
        with open(self.file1, 'r') as f:
            assertx(f.read(), '==', 'hello world')

    def teardown(self):
        """
        Clean up test environment.
        """
        shutil.rmtree(self.workdir)
        self.info('Removed workdir: %s', self.workdir)
        self.sleep(1)
