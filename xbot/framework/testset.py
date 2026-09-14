# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Testcase list management.
"""

import os

from typing import Any, NamedTuple
from functools import cached_property
from pathlib import PurePosixPath
from importlib import import_module

from ruamel import yaml

from xbot.framework.testcase import TestCase
from xbot.framework.utils import ordered_walk
from xbot.framework.errors import TestSetError, SuperClassError

class TestCases(NamedTuple):
    """
    The type returned after parsing `TestSet.testcases` in the testset.
    """
    install: tuple[str, ...]
    test: tuple[str, ...]


class TestSet(object):
    """
    Testcase list manager.
    """
    def __init__(self, filepath: str) -> None:
        """
        :param filepath: testset filepath.
        :return: None.
        """
        self.__data: dict[str, Any] = self.__parse(filepath)
        self.superclses  # Import and check in advance.

    def __parse(self, filepath: str) -> dict[str, Any]:
        """
        Parse testset.

        :param filepath: testset filepath.
        :return: parsed testset data.
        """
        with open(filepath, encoding='utf8') as f:
            data = yaml.YAML(typ='safe').load(f)
            if not isinstance(data, dict):
                raise TestSetError('Testset is not a dict.')
            if 'tags' not in data:
                raise TestSetError('No `tags` found in testset.')
            if not isinstance(data['tags'], dict):
                raise TestSetError('`tags` is not a dict.')
            if 'include' not in data['tags']:
                raise TestSetError('No `tags.include` found in testset.')
            if data['tags']['include'] and not isinstance(data['tags']['include'], list):
                raise TestSetError('`tags.include` is not a list.')
            if 'exclude' not in data['tags']:
                raise TestSetError('No `tags.exclude` found in testset.')
            if data['tags']['exclude'] and not isinstance(data['tags']['exclude'], list):
                raise TestSetError('`tags.exclude` is not a list.')
            if 'testcases' not in data:
                raise TestSetError('No `testcases` found in testset.')
            if not isinstance(data['testcases'], dict):
                raise TestSetError('`testcases` is not a dict.')
            for f in ('install', 'test'):
                if f not in data['testcases']:
                    raise TestSetError(f'No `testcases.{f}` found in testset.')
                v = data['testcases'][f]
                if v is not None and not isinstance(v, list):
                    raise TestSetError(f'`testcases.{f}` is not a list.')
                if v:
                    for p in v:
                        if not os.path.exists(p):
                            raise TestSetError(f'Path `{p}` does not exist.')
            return data

    @cached_property
    def include_tags(self) -> tuple[str, ...]:
        """
        tags used to include testcases.
        """
        include_tags = self.__data['tags'].get('include') or []
        return tuple(include_tags)

    @cached_property
    def exclude_tags(self) -> tuple[str, ...]:
        """
        tags used to exclude testcases.
        """
        exclude_tags = self.__data['tags'].get('exclude') or []
        return tuple(exclude_tags)

    @cached_property
    def testcases(self) -> TestCases:
        """
        testcases list.
        """
        testcases = {'install': [], 'test': []}
        for section in ('install', 'test'):
            paths = self.__data['testcases'][section]
            if not paths:
                continue
            for path in paths:
                if path.endswith('.py'):
                    testcases[section].append(path)
                else:
                    for top, dirs, files in ordered_walk(path):
                        for file in sorted(files):
                            if file.startswith('tc_') and file.endswith('.py'):
                                relpath = os.path.relpath(os.path.join(top, file), os.getcwd())
                                testcases[section].append(relpath.replace(os.sep, '/'))
        return TestCases(install=tuple(testcases['install']),
                         test=tuple(testcases['test']))

    @cached_property
    def superclses(self) -> dict[PurePosixPath, type[TestCase]]:
        """
        Super classes of all testcases.
        """
        superclses = {}
        for tc in (self.testcases.install + self.testcases.test):
            # Grandfather class.
            grandfathercls = TestCase
            # From top to bottom.
            for parentpath in reversed(PurePosixPath(tc).parents[:-1]):
                # Has been imported.
                if parentpath in superclses:
                    grandfathercls = superclses[parentpath]
                    continue
                # The current directory is definitely the project root, so 
                # relative path imports can be used here. Refer to `main.py:run()`.
                supermod = import_module(str(parentpath).replace('/', '.'))
                for obj in vars(supermod).values():
                    # The first subclass of `TestCase` defined in the 
                    # current module will be treated as the superclass.
                    if isinstance(obj, type) and \
                            obj.__module__ == supermod.__name__ and \
                            issubclass(obj, TestCase):
                        parentcls = obj
                        parentclsloc = (f'{parentpath}/__init__.py:{parentcls.__name__}')
                        if not issubclass(parentcls, grandfathercls):
                            grandfatherpath = PurePosixPath(parentpath).parent
                            grandfatherclsloc = f'{grandfatherpath}/__init__.py:{grandfathercls.__name__}'
                            raise SuperClassError(f'{parentclsloc} must inherit from {grandfatherclsloc}')
                        for method in ('setup', 'teardown'):
                            if method not in parentcls.__dict__:
                                raise SuperClassError(f'{parentclsloc} did not reimplement `{method}` method.')
                        superclses[parentpath] = parentcls
                        grandfathercls = parentcls
                        break
                else:
                    raise SuperClassError(f'No superclass (subclass of {grandfathercls.__name__}) was found in {parentpath}/__init__.py')
        return superclses
