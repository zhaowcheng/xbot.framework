import os
import unittest
import tempfile
import shutil

from unittest.mock import patch, mock_open

from xbot.testset import TestSet, TestSetError

class TestTestSet(unittest.TestCase):
    """
    测试套单元测试。
    """
    @classmethod
    def setUpClass(cls):
        """
        创建一个临时目录，并在其中创建如下目录结构：
        testcases
        ├── __init__.py
        ├── dir1
        │   ├── tc_01.py
        │   └── tc_02.py
        └── dir2
            ├── __init__.py
            ├── subdir2_1
            │   ├── __init__.py
            │   ├── tc_05.py
            │   └── tc_06.py
            ├── tc_03.py
            └── tc_04.py
        """
        cls.tmpdir = tempfile.mkdtemp()
        dir1 = os.path.join(cls.tmpdir, 'testcases', 'dir1')
        dir2 = os.path.join(cls.tmpdir, 'testcases', 'dir2')
        subdir2_1 = os.path.join(cls.tmpdir, 'testcases', 'dir2', 'subdir2_1')
        for d in [dir1, dir2, subdir2_1]:
            os.makedirs(d)
            with open(os.path.join(d, '__init__.py'), 'w', encoding='utf8'):
                pass
        tc1 = os.path.join(dir1, 'tc_01.py')
        tc2 = os.path.join(dir1, 'tc_02.py')
        tc3 = os.path.join(dir2, 'tc_03.py')
        tc4 = os.path.join(dir2, 'tc_04.py')
        tc5 = os.path.join(subdir2_1, 'tc_05.py')
        tc6 = os.path.join(subdir2_1, 'tc_06.py')
        txtfile = os.path.join(subdir2_1, 'testfile.txt')
        for tc in [tc1, tc2, tc3, tc4, tc5, tc6, txtfile]:
            with open(tc, 'w', encoding='utf8'):
                pass
        cls.oldcwd = os.getcwd()
        os.chdir(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.oldcwd)
        shutil.rmtree(cls.tmpdir)

    def mock_testset(self, content: str) -> TestSet:
        """
        模拟测试套。
        """
        with patch("builtins.open", mock_open(read_data=content)):
            return TestSet('testset.yml')
    
    def test_tags(self):
        """
        测试 include_tags 属性。
        """
        content = """
        tags:
          include:
            - tag1
            - tag2
          exclude:
            - tag3
            - tag4
        paths:
        """
        testset = self.mock_testset(content)
        self.assertEqual(testset.include_tags, ('tag1', 'tag2'))
        self.assertEqual(testset.exclude_tags, ('tag3', 'tag4'))

    def test_tags_empty(self):
        """
        测试 include_tags 属性为空。
        """
        content = """
        tags:
          include:
          exclude:
        paths:
        """
        testset = self.mock_testset(content)
        self.assertEqual(testset.include_tags, tuple())
        self.assertEqual(testset.exclude_tags, tuple())

    def test_tags_not_dict(self):
        """
        测试 tags 属性不是字典。
        """
        content = """
        tags:
          - tag1
          - tag2
        paths:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)
    
    def test_include_tags_not_list(self):
        """
        测试 include_tags 属性不是列表。
        """
        content = """
        tags:
          include: tag1
          exclude:
            - tag3
            - tag4
        paths:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)

    def test_exclude_tags_not_list(self):
        """
        测试 exclude_tags 属性不是列表。
        """
        content = """
        tags:
          include:
            - tag1
            - tag2
          exclude: tag3
        paths:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)

    def test_include_tags_not_found(self):
        """
        测试 tags.include 属性不存在。
        """
        content = """
        tags:
          exclude:
            - tag3
            - tag4
        paths:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)

    def test_exclude_tags_not_found(self):
        """
        测试 tags.exclude 属性不存在。
        """
        content = """
        tags:
          include:
            - tag1
            - tag2
        paths:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)

    def test_paths(self):
        """
        测试 paths 属性。
        """
        content = """
        tags:
          include:
          exclude:
        paths:
          - testcases/dir1/tc_01.py
          - testcases/dir2
        """
        testset = self.mock_testset(content)
        self.assertEqual(testset.paths, (
            'testcases/dir1/tc_01.py',
            'testcases/dir2/tc_03.py',
            'testcases/dir2/tc_04.py',
            'testcases/dir2/subdir2_1/tc_05.py',
            'testcases/dir2/subdir2_1/tc_06.py'
        ))

    def test_path_not_exist(self):
        """
        测试 paths 属性中的路径不存在。
        """
        content = """
        tags:
          include:
          exclude:
        paths:
          - testcases/dir1/tc_00.py
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content).paths


if __name__ == '__main__':
    unittest.main(verbosity=2)
