# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Testcase list management.
"""

import os

from ruamel import yaml

from xbot.framework.utils import ordered_walk
from xbot.framework.errors import TestSetError


class TestSet(object):
    """
    Testcase list manager.
    """
    def __init__(self, filepath: str):
        """
        :param filepath: testset filepath.
        """
        self._data = self._parse(filepath)
        self._include_tags = None
        self._exclude_tags = None
        self._paths = None

    def _parse(self, filepath: str) -> dict:
        """
        Parse testset.
        """
        with open(filepath, encoding='utf8') as f:
            data = yaml.YAML(typ='safe').load(f)
            if 'tags' not in data:
                raise TestSetError('No `tags` found in testset.')
            if not isinstance(data['tags'], dict):
                raise TestSetError('`tags` should be a dict.')
            if 'include' not in data['tags']:
                raise TestSetError('No `tags.include` found in testset.')
            if data['tags']['include'] and not isinstance(data['tags']['include'], list):
                raise TestSetError('`tags.include` should be a list.')
            if 'exclude' not in data['tags']:
                raise TestSetError('No `tags.exclude` found in testset.')
            if data['tags']['exclude'] and not isinstance(data['tags']['exclude'], list):
                raise TestSetError('`tags.exclude` should be a list.')
            if 'paths' not in data:
                raise TestSetError('No `paths` found in testset.')
            if data['paths'] and not isinstance(data['paths'], list):
                raise TestSetError('`paths` should be a list.')
            return data

    @property
    def include_tags(self) -> tuple:
        """
        tags used to include testcases.
        """
        if not self._include_tags:
            self._include_tags = self._data['tags'].get('include') or []
        return tuple(self._include_tags)

    @property
    def exclude_tags(self) -> tuple:
        """
        tags used to exclude testcases.
        """
        if not self._exclude_tags:
            self._exclude_tags = self._data['tags'].get('exclude') or []
        return tuple(self._exclude_tags)

    @property
    def paths(self) -> tuple:
        """
        testcase filepath(relative) list.
        """
        if not self._paths:
            paths = []
            for p in self._data['paths']:
                if not os.path.exists(p):
                    raise TestSetError('Path `%s` does not exist.' % p)
                if p.endswith('.py'):
                    paths.append(p)
                else:
                    for top, dirs, files in ordered_walk(p):
                        for f in sorted(files):
                            if f.startswith('tc_') and f.endswith('.py'):
                                relpath = os.path.relpath(os.path.join(top, f), 
                                                          os.getcwd())
                                paths.append(relpath.replace(os.sep, '/'))
            self._paths = paths
        return tuple(self._paths)
