# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试套模块。
"""

import os

from ruamel import yaml
from copy import deepcopy

from xbot.utils import ordered_walk
from xbot.errors import TestSetError


class TestSet(object):
    """
    测试套类。
    """
    def __init__(self, filepath: str):
        """
        :param filepath: 测试套文件路径。
        """
        self._data = self._parse(filepath)
        self._include_tags = None
        self._exclude_tags = None
        self._paths = None

    def _parse(self, filepath: str) -> dict:
        """
        解析测试套。
        """
        with open(filepath) as f:
            return yaml.YAML(typ='safe').load(f)

    @property
    def include_tags(self) -> list:
        """
        用来筛选用例的 tags。
        """
        if not self._include_tags:
            self._include_tags = self._data['tags'].get('include') or []
        return deepcopy(self._include_tags)

    @property
    def exclude_tags(self) -> list:
        """
        用来排除用例的 tags。
        """
        if not self._exclude_tags:
            self._exclude_tags = self._data['tags'].get('exclude') or []
        return deepcopy(self._exclude_tags)

    @property
    def paths(self) -> tuple:
        """
        待执行的测试用例或目录路径列表。
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
                            if f.endswith('.py') and f != '__init__.py':
                                relpath = os.path.relpath(os.path.join(top, f), 
                                                          os.getcwd())
                                paths.append(relpath.replace(os.sep, '/'))
            self._paths = paths
        return tuple(self._paths)
