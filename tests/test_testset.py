import os
import shutil
import sys
import tempfile
import unittest

from pathlib import PurePosixPath
from unittest.mock import mock_open, patch

from xbot.framework.errors import SuperClassError
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
        initfiles = {
            os.path.join(cls.tmpdir, 'testcases', '__init__.py'): """
from xbot.framework.testcase import TestCase


class tc(TestCase):
    def setup(self):
        pass

    def teardown(self):
        pass
""",
            os.path.join(dir1, '__init__.py'): """
from testcases import tc


class tc_dir1(tc):
    def setup(self):
        pass

    def teardown(self):
        pass
""",
            os.path.join(dir2, '__init__.py'): """
from testcases import tc


class tc_dir2(tc):
    def setup(self):
        pass

    def teardown(self):
        pass
""",
            os.path.join(subdir2_1, '__init__.py'): """
from testcases.dir2 import tc_dir2


class tc_subdir2_1(tc_dir2):
    def setup(self):
        pass

    def teardown(self):
        pass
""",
        }
        for path, content in initfiles.items():
            with open(path, 'w', encoding='utf8') as initfile:
                initfile.write(content)
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
        sys.path.insert(0, cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        cls._clear_project_modules()
        sys.path.remove(cls.tmpdir)
        os.chdir(cls.oldcwd)
        shutil.rmtree(cls.tmpdir)

    @staticmethod
    def _clear_project_modules() -> None:
        """
        Remove modules imported from the temporary project.

        :return: None.
        """
        for name in tuple(sys.modules):
            if name == 'testcases' or name.startswith('testcases.'):
                del sys.modules[name]

    def mock_testset(self, content: str) -> TestSet:
        """
        Mock a TestSet object.

        :param content: Testset YAML content.
        :return: TestSet object.
        """
        self._clear_project_modules()
        with patch('builtins.open', mock_open(read_data=content)):
            return TestSet('testset.yml')

    def create_superclass_scenario(
        self,
        name: str,
        init_content: str,
    ) -> str:
        """
        Create one superclass validation scenario.

        :param name: Testcase directory name.
        :param init_content: Directory initializer content.
        :return: Testcase path.
        """
        directory = os.path.join(self.tmpdir, 'testcases', name)
        os.makedirs(directory, exist_ok=True)
        with open(
            os.path.join(directory, '__init__.py'),
            'w',
            encoding='utf8',
        ) as initfile:
            initfile.write(init_content)
        casepath = f'testcases/{name}/tc_case.py'
        with open(casepath, 'w', encoding='utf8'):
            pass
        return casepath

    def test_superclasses(self):
        """
        Parse a valid multi-level superclass hierarchy.
        """
        content = """
        tags:
          include:
          exclude:
        testcases:
          install:
          test:
            - testcases/dir2/subdir2_1/tc_05.py
        """
        superclses = self.mock_testset(content).superclses
        self.assertEqual(
            tuple(superclses),
            (
                PurePosixPath('testcases'),
                PurePosixPath('testcases/dir2'),
                PurePosixPath('testcases/dir2/subdir2_1'),
            ),
        )
        self.assertEqual(superclses[PurePosixPath('testcases')].__name__, 'tc')
        self.assertTrue(
            issubclass(
                superclses[PurePosixPath('testcases/dir2/subdir2_1')],
                superclses[PurePosixPath('testcases/dir2')],
            ),
        )

    def test_superclass_validation(self):
        """
        Reject missing, unrelated, and incomplete superclasses.
        """
        scenarios = (
            ('missing', '', 'No superclass .* testcases/missing/__init__.py'),
            (
                'unrelated',
                """
from xbot.framework.testcase import TestCase


class tc_unrelated(TestCase):
    def setup(self):
        pass

    def teardown(self):
        pass
""",
                'testcases/unrelated/__init__.py:tc_unrelated must inherit '
                'from testcases/__init__.py:tc',
            ),
            (
                'missing_setup',
                """
from testcases import tc


class tc_missing_setup(tc):
    def teardown(self):
        pass
""",
                'testcases/missing_setup/__init__.py:tc_missing_setup did not '
                'reimplement `setup` method',
            ),
            (
                'missing_teardown',
                """
from testcases import tc


class tc_missing_teardown(tc):
    def setup(self):
        pass
""",
                'testcases/missing_teardown/__init__.py:tc_missing_teardown '
                'did not reimplement `teardown` method',
            ),
        )
        for name, init_content, error in scenarios:
            with self.subTest(name=name):
                casepath = self.create_superclass_scenario(name, init_content)
                content = f"""
                tags:
                  include:
                  exclude:
                testcases:
                  install:
                  test:
                    - {casepath}
                """
                with self.assertRaisesRegex(SuperClassError, error):
                    self.mock_testset(content)

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
