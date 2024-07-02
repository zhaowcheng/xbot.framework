# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Test environment information management.
"""

import os

import jmespath

from typing import Any

from ruamel import yaml


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

    def get(self, expr: str) -> Any:
        """
        Get value from testbed.

        https://jmespath.org/

        :param expr: JMESPath expression.
        :return: Got value.

        ----------yamlfile--------
        a:
          b1: c
          b2:
            - 1
            - 2
            - 3
          b3:
            - x: 1
              y: 'h'
            - x: 2
              y: 'i'
        ---------------------------

        >>> get("a.b1")
        'c'
        >>> get("a.b2[0]")
        1
        >>> get("a.b3") == None
        True
        >>> get("a.b3[0].x")
        [1]
        >>> get('a.b3[?x==`1`]')
        [{'x': 1, 'y': 'h'}]
        >>> get("a.b3[?y=='i']|[0]")
        {'x': 2, 'y': 'i'}
        >>> get('a.b3[?x==`3`]') == None
        True
        """
        return jmespath.search(expr, self.__data)
