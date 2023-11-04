# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
TestSet management.
"""

import os
import textwrap

from ruamel import yaml

from xbot.errors import TestSetError


class TestSet(object):
    """
    TestSet management.
    """
    def __init__(self, filepath):
        """
        :param filepath: Testset filepath。
        """
        self._data = self._parse(filepath)
        self._include_tags = None
        self._exclude_tags = None
        self._paths = None

    def _parse(self, filepath):
        """
        Parse testset file.
        """
        with open(filepath) as f:
            return yaml.safe_load(f)

    @property
    def include_tags(self):
        """
        Include tags in testset.
        """
        if not self._include_tags:
            self._include_tags = self._data['tags'].get('include') or []
        return tuple(self._include_tags)

    @property
    def exclude_tags(self):
        """
        Exclude tags in testset.
        """
        if not self._exclude_tags:
            self._exclude_tags = self._data['tags'].get('exclude') or []
        return tuple(self._exclude_tags)

    @property
    def paths(self):
        """
        Testcase paths.
        """
        if not self._paths:
            paths = []
            for p in self._data['paths']:
                if not os.path.exists(p):
                    raise TestSetError(f'Path `{p}` does not exist.')
                if p.endswith('.py'):
                    paths.append(p)
                else:
                    for top, dirs, files in os.walk(p):
                        for f in files:
                            if f.endswith('.py') and f != '__init__.py':
                                relpath = os.path.relpath(os.path.join(top, f), 
                                                          os.getcwd())
                                paths.append(relpath.replace(os.sep, '/'))
            self._paths = paths
        return tuple(self._paths)
