# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试床相关模块。
"""

import os


from functools import cache
from collections import UserDict
from typing import Any, Optional
from ruamel import yaml
from jsonschema import validate
from lib import common
from lib.ssh import SSH
from lib.util import deepget


class TestbedError(Exception):
    """
    测试床文件错误。
    """
    pass


class TestBed(object):
    """
    测试床。
    """
    def __init__(self, filepath: str) -> None:
        """
        :param filepath: 测试床文件路径。
        """
        self.__data = self.__parse(filepath)
        self.__name = os.path.basename(filepath).rsplit('.', 1)[0]

    def __parse(self, filepath: str) -> Any:
        """
        解析并验证测试床文件。
        """
        with open(filepath) as f:
            data = yaml.safe_load(f)
            if 'testbed' not in data:
                raise TestbedError('Missing `testbed` key.')
            if 'schema' not in data:
                raise TestbedError('Missing `schema` key.')
            try:
                validate(data['testbed'], data['schema'])
            except Exception as e:
                raise TestbedError(str(e)) from None
            return data['testbed']

    @property
    def name(self) -> str:
        """
        测试床名称。
        """
        return self.__name
    
    @cached_property
    def content(self) -> str:
        """
        测试床文件内容。
        """
        return yaml.safe_dump(self.__data, default_flow_style=True)

    def get(self, deepkey: str, default: Optional[Any] = None) -> Any:
        """
        ----------yamlfile--------
        a:
          b1: c
          b2:
            - 1
            - 2
            - 3
        ---------------------------
        >>> get('a.b1')
        'c'
        >>> get('a.b2[0]')
        1
        >>> get('a.b3', default='x')
        'x'
        """
        try:
            return deepget(self.__data, key)
        except KeyError:
            return default

    @cache
    def ssh(self, host: str, user: str, password: str, sshport: int = 22) -> SSH:
        """
        获取 SSH 连接。
        """
        return SSH(host, user, password, sshport)
