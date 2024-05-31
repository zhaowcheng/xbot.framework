# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试床模块。
"""

import os

from typing import Any

from ruamel import yaml
from xbot.utils import deepget


class TestBed(object):
    """
    测试床类。
    """
    def __init__(self, filepath: str):
        """
        :param filepath: 测试床文件路径。
        """
        self.__data = self.__parse(filepath)
        self.__name = os.path.basename(filepath).rsplit('.', 1)[0]
        with open(filepath, encoding='utf8') as f:
            self.__content = f.read()

    def __parse(self, filepath: str) -> dict:
        """
        解析测试床。
        """
        with open(filepath, encoding='utf8') as f:
            return yaml.YAML(typ='safe').load(f)

    @property
    def name(self) -> str:
        """
        测试床名称（不带后缀的文件名）。
        """
        return self.__name
    
    @property
    def content(self) -> str:
        """
        测试床文件内容。
        """
        return self.__content

    def get(self, deepkey: str, default: Any = None) -> Any:
        """
        获取指定路径的值。

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

        :param deepkey: 用 `.` 连接的路径。
        :param default: 如果路径不存在返回的默认值。
        :return: 获取到的值或默认值。
        """
        try:
            return deepget(self.__data, deepkey)
        except KeyError:
            return default
