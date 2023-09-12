# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试套相关模块。
"""

import os
import textwrap

from functools import cached_property
from typing import Any, List, Tuple
from ruamel import yaml
from jsonschema import validate

from lib import common


class TestsetError(Exception):
    """
    测试套文件错误。
    """
    pass


class TestSet(object):
    """
    测试套。
    """
    def __init__(self, filepath: str) -> None:
        """
        :param filepath: 测试套文件路径。
        """
        self._data = self._parse(filepath)

    def _parse(self, filepath: str) -> Any:
        """
        解析并验证测试套文件。
        """
        with open(filepath) as f:
            data = yaml.safe_load(f)
            if 'testset' not in data:
                raise TestsetError('Missing `testset` key.')
            if 'schema' not in data:
                raise TestsetError('Missing `schema` key.')
            try:
                validate(data['testset'], data['schema'])
            except Exception as e:
                raise TestsetError(str(e)) from None
            return data['testset']

    @cached_property
    def include_tags(self) -> Tuple[str]:
        """
        测试套中包含类标签。
        """
        return tuple(self._data['tags'].get('include') or [])

    @cached_property
    def exclude_tags(self) -> Tuple[str]:
        """
        测试套中排除类标签。
        """
        return tuple(self._data['tags'].get('exclude') or [])

    @cached_property
    def paths(self) -> Tuple[str]:
        """
        测试套中的路径。
        """
        paths = []
        for p in self._data['paths']:
            abspath = os.path.normpath(os.path.join(common.XBOT_DIR, p))
            if not os.path.exists(abspath):
                raise TestsetError(f'Path `{p}` does not exist.')
            if p.endswith('.py'):
                paths.append(p)
            else:
                for top, dirs, files in os.walk(abspath):
                    for f in files:
                        if f.endswith('.py') and f != '__init__.py':
                            relpath = os.path.relpath(os.path.join(top, f), 
                                                      common.XBOT_DIR)
                            paths.append(relpath.replace(os.sep, '/'))
        return paths
