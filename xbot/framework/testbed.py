# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Test environment information management.
"""

import os

from typing import Any

from ruamel import yaml
from xbot.framework.utils import deepget


class TestBed(object):
    """
    Test environment information manager.
    """
    def __init__(self, filepath: str):
        """
        :param filepath: testbed filepath.
        """
        self.__data = self.__parse(filepath)
        self.__name = os.path.basename(filepath).rsplit('.', 1)[0]
        with open(filepath, encoding='utf8') as f:
            self.__content = f.read()

    def __parse(self, filepath: str) -> dict:
        """
        Parse testbed.
        """
        with open(filepath, encoding='utf8') as f:
            return yaml.YAML(typ='safe').load(f)

    @property
    def name(self) -> str:
        """
        testbed filename(without suffix).
        """
        return self.__name
    
    @property
    def content(self) -> str:
        """
        testbed file content.
        """
        return self.__content

    def get(self, deepkey: str, default: Any = None) -> Any:
        """
        Get value from testbed.

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

        :param deepkey: multiple keys combined with `.`
        :param default: return value when deepkey not exists.
        :return: Got value.
        """
        try:
            return deepget(self.__data, deepkey)
        except KeyError:
            return default
