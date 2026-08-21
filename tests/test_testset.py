import os
import unittest
import tempfile
import shutil

from unittest.mock import patch, mock_open

from xbot.framework.testset import TestCases, TestSet, TestSetError

class TestTestSet(unittest.TestCase):
    """
    Unit tests for testset module.
    """
    @classmethod
    def setUpClass(cls):
        """
        Create a temporary directory and some testcases:

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
        Mock a TestSet object.
        """
        with patch("builtins.open", mock_open(read_data=content)):
            return TestSet('testset.yml')

    def test_document_not_dict(self):
        """
        Expect TestSetError when the document is not a dict.
        """
        contents = ('', '- testset')
        for content in contents:
            with self.subTest(content=content):
                with self.assertRaisesRegex(
                    TestSetError,
                    'Testset is not a dict',
                ):
                    self.mock_testset(content)
    
    def test_tags(self):
        """
        Test tags property.
        """
        content = """
        tags:
          include:
            - tag1
            - tag2
          exclude:
            - tag3
            - tag4
        testcases:
          install:
          test:
        """
        testset = self.mock_testset(content)
        self.assertEqual(testset.include_tags, ('tag1', 'tag2'))
        self.assertEqual(testset.exclude_tags, ('tag3', 'tag4'))

    def test_tags_empty(self):
        """
        Expect empty tuple when tags is empty.
        """
        content = """
        tags:
          include:
          exclude:
        testcases:
          install:
          test:
        """
        testset = self.mock_testset(content)
        self.assertEqual(testset.include_tags, tuple())
        self.assertEqual(testset.exclude_tags, tuple())

    def test_tags_not_dict(self):
        """
        Expect TestSetError when tags is not a dict.
        """
        content = """
        tags:
          - tag1
          - tag2
        testcases:
          install:
          test:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)
    
    def test_include_tags_not_list(self):
        """
        Expect TestSetError when tags.include is not a list.
        """
        content = """
        tags:
          include: tag1
          exclude:
            - tag3
            - tag4
        testcases:
          install:
          test:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)

    def test_exclude_tags_not_list(self):
        """
        Expect TestSetError when tags.exclude is not a list.
        """
        content = """
        tags:
          include:
            - tag1
            - tag2
          exclude: tag3
        testcases:
          install:
          test:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)

    def test_include_tags_not_found(self):
        """
        Expect TestSetError when tags.include is not found.
        """
        content = """
        tags:
          exclude:
            - tag3
            - tag4
        testcases:
          install:
          test:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)

    def test_exclude_tags_not_found(self):
        """
        Expect TestSetError when tags.exclude is not found.
        """
        content = """
        tags:
          include:
            - tag1
            - tag2
        testcases:
          install:
          test:
        """
        with self.assertRaises(TestSetError):
            self.mock_testset(content)

    def test_testcases(self):
        """
        Test testcase groups and directory expansion.
        """
        content = """
        tags:
          include:
          exclude:
        testcases:
          install:
            - testcases/dir1/tc_01.py
          test:
            - testcases/dir2
        """
        testset = self.mock_testset(content)
        self.assertEqual(
            testset.testcases,
            TestCases(
                install=('testcases/dir1/tc_01.py',),
                test=(
                    'testcases/dir2/tc_03.py',
                    'testcases/dir2/tc_04.py',
                    'testcases/dir2/subdir2_1/tc_05.py',
                    'testcases/dir2/subdir2_1/tc_06.py',
                ),
            ),
        )

    def test_testcases_empty(self):
        """
        Expect empty tuples when testcase groups are empty.
        """
        content = """
        tags:
          include:
          exclude:
        testcases:
          install:
          test:
        """
        self.assertEqual(
            self.mock_testset(content).testcases,
            TestCases(install=(), test=()),
        )

    def test_testcases_not_found(self):
        """
        Expect TestSetError when testcases is not found.
        """
        content = """
        tags:
          include:
          exclude:
        """
        with self.assertRaisesRegex(TestSetError, 'No `testcases`'):
            self.mock_testset(content)

    def test_testcases_not_dict(self):
        """
        Expect TestSetError when testcases is not a dict.
        """
        contents = (
            """
            tags:
              include:
              exclude:
            testcases:
            """,
            """
            tags:
              include:
              exclude:
            testcases: []
            """,
        )
        for content in contents:
            with self.subTest(content=content):
                with self.assertRaisesRegex(
                    TestSetError,
                    '`testcases` is not a dict',
                ):
                    self.mock_testset(content)

    def test_testcase_group_not_found(self):
        """
        Expect TestSetError when a testcase group is not found.
        """
        contents = (
            """
            tags:
              include:
              exclude:
            testcases:
              test:
            """,
            """
            tags:
              include:
              exclude:
            testcases:
              install:
            """,
        )
        for content in contents:
            with self.subTest(content=content):
                with self.assertRaises(TestSetError):
                    self.mock_testset(content)

    def test_testcase_group_not_list(self):
        """
        Expect TestSetError when a non-empty testcase group is not a list.
        """
        content = """
        tags:
          include:
          exclude:
        testcases:
          install: testcases/dir1/tc_01.py
          test:
        """
        with self.assertRaisesRegex(
            TestSetError,
            '`testcases.install` is not a list',
        ):
            self.mock_testset(content)

    def test_empty_testcase_group_not_list(self):
        """
        Expect TestSetError when an empty testcase group is not a list.
        """
        values = ('{}', '0')
        for value in values:
            content = f"""
            tags:
              include:
              exclude:
            testcases:
              install: {value}
              test:
            """
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    TestSetError,
                    '`testcases.install` is not a list',
                ):
                    self.mock_testset(content)

    def test_testcase_path_not_exist(self):
        """
        Expect TestSetError when a testcase path does not exist.
        """
        content = """
        tags:
          include:
          exclude:
        testcases:
          install:
          test:
            - testcases/dir1/tc_00.py
        """
        with self.assertRaisesRegex(TestSetError, 'does not exist'):
            self.mock_testset(content)


if __name__ == '__main__':
    unittest.main(verbosity=2)
