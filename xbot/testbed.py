# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
TestBed management.
"""

import os

from ruamel import yaml
from xbot.util import deepget


class TestBed(object):
    """
    TestBed management.
    """
    def __init__(self, filepath):
        """
        :param filepath: Testbed filepath。
        """
        self.__data = self.__parse(filepath)
        self.__name = os.path.basename(filepath).rsplit('.', 1)[0]
        with open(filepath) as f:
            self.__content = f.read()

    def __parse(self, filepath):
        """
        Parse testbed file.
        """
        with open(filepath) as f:
            return yaml.safe_load(f)

    @property
    def name(self):
        """
        Testbed name.
        """
        return self.__name
    
    @property
    def content(self):
        """
        Testbed file content.
        """
        return self.__content

    def get(self, deepkey, default=None):
        """
        Get value from testbed file.

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

        :param deepkey: Key paths separated by dot.
        :param default: Default value if key not exists.
        :return: value.
        """
        try:
            return deepget(self.__data, key)
        except KeyError:
            return default
