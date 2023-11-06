import os
import tempfile
import shutil

from lib.testcase import TestCase


# The class name will be treated as the testcase id, 
# and should be consistent with the file name.
class tc_eg_02(TestCase):
    """
    Test creation of directory and file.

    @TestcaseName: Test creation of directory and file.

    @PresetSteps:
        1. Create a temporary workdir;

    @TestSteps:
        1. Create directory `dir1` in workdir;
        2. Create empty file `file1` in `dir1`;
        3. Write `hello world` to `file1`;
        
    @ExpectedResults:
        1. `dir1` should be created;
        2. `file1` should be created;
        3. `file1` should contain `hello world`;
    """

    # Max execution time(minutes).
    TIMEOUT = 5
    # Testcase tags.
    TAGS = ['tag2']

    def setup(self):
        """
        Preset steps.
        """
        self.workdir = tempfile.mkdtemp()
        self.info(f'Created workdir: {self.workdir}')

    def process(self):
        """
        Test steps.
        """
        # Test step 1
        self.info('Start test step 1')
        dir1 = os.path.join(self.workdir, 'dir1')
        os.mkdir(dir1)
        self.assertx(os.path.exists(dir1), '==', True)

        # Test step 2
        self.info('Start test step 2')
        file1 = os.path.join(dir1, 'file1')
        open(file1, 'w').close()
        self.sleep(1)
        self.assertx(os.path.exists(file1), '==', True)

        # Test step 3
        self.info('Start test step 3')
        with open(file1, 'w') as f:
            f.write('hello world')
        with open(file1, 'r') as f:
            self.assertx(f.read(), '==', 'hello world')

    def teardown(self):
        """
        Post steps.
        """
        self.info('Start teardown')
        shutil.rmtree(self.workdir)
        self.info(f'Removed workdir: {self.workdir}')
