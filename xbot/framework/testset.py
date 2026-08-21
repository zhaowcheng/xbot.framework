# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Testcase list management.
"""

import os

from typing import Any, NamedTuple
from functools import cached_property

from ruamel import yaml

from xbot.framework.utils import ordered_walk
from xbot.framework.errors import TestSetError

class TestCases(NamedTuple):
    """
    测试套中 `TestSet.testcases` 解析后返回的类型。
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
        self._data: dict[str, Any] = self._parse(filepath)

    def _parse(self, filepath: str) -> dict[str, Any]:
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
        include_tags = self._data['tags'].get('include') or []
        return tuple(include_tags)

    @cached_property
    def exclude_tags(self) -> tuple[str, ...]:
        """
        tags used to exclude testcases.
        """
        exclude_tags = self._data['tags'].get('exclude') or []
        return tuple(exclude_tags)

    @cached_property
    def testcases(self) -> TestCases:
        """
        testcases list.
        """
        testcases = {'install': [], 'test': []}
        for section in ('install', 'test'):
            paths = self._data['testcases'][section]
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
