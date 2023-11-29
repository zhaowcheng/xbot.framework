import os
import tempfile
import shutil

from xbot.util import assertx

from lib.testcase import TestCase


# The class name will be treated as the testcase id, 
# and should be consistent with the file name.
class tc_eg_02(TestCase):
    """
    Test creation of directory and file.
    """
    # Max execution time(seconds).
    TIMEOUT = 60
    # Stop the test run on the first fail.
    FAILFAST = True
    # Testcase tags.
    TAGS = ['tag1']

    def setup(self):
        """
        Create a temporary workdir.
        """
        self.workdir = tempfile.mkdtemp()
        self.info('Created workdir: %s', self.workdir)

    def step1(self):
        """
        Create directory `dir1` in workdir and check 
        that it should be created successfully.
        """
        self.dir1 = os.path.join(self.workdir, 'dir1')
        os.mkdir(self.dir1)
        assertx(os.path.exists(self.dir1), '==', True)

    def step2(self):
        """
        Create empty file `file1` in `dir1` and check 
        that it should be created successfully.
        """
        self.file1 = os.path.join(self.dir1, 'file1')
        open(self.file1, 'w').close()
        assertx(os.path.exists(self.file1), '==', True)

    def step3(self):
        """
        Write `hello world` to `file1` and check
        that it should be wrote successfully.
        """
        with open(self.file1, 'w') as f:
            f.write('hello world')
        with open(self.file1, 'r') as f:
            assertx(f.read(), '==', 'hello world')

    def teardown(self):
        """
        Remove the temporary workdir.
        """
        shutil.rmtree(self.workdir)
        self.info('Removed workdir: %s', self.workdir)
        self.sleep(1)
