# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试床相关模块。
"""

import os
import lxml.etree

from functools import cache
from typing import Any
from lib import common
from lib.ssh import SSH


class TestbedError(Exception):
    """
    测试床文件错误。
    """
    pass


class TestbedSchemaError(Exception):
    """
    测试床 schema 文件错误。
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
        self._etree = self._parse(filepath)
        self._name = os.path.basename(filepath).replace('.xml', '')
        with open(filepath) as f:
            self._content = f.read()

    def _parse(self, filepath: str) -> Any:
        """
        解析并验证测试床文件。
        """
        testbed_etree = lxml.etree.parse(filepath)
        testbed_etree_root = lxml.etree.parse(filepath).getroot()
        if testbed_etree_root.tag != 'testbed':
            raise TestbedError(
                'The tag of the root element must be `testbed`, ' \
                f'but now is `{testbed_etree_root.tag}`.'
            )
        schema_filename = testbed_etree_root.attrib.get('schema')
        if schema_filename:
            schema_filepath = os.path.join(common.TESTBED_DIR, schema_filename)
            if not os.path.exists(schema_filepath):
                raise TestbedError(
                    f'The schema file `{schema_filename}` ' \
                    f'does not exist in `{common.TESTBED_DIR}`.'
                )
            try:
                schema_etree = lxml.etree.parse(schema_filepath)
            except lxml.etree.XMLSchemaError as e:
                raise TestbedSchemaError(f'{str(e)}({schema_filepath})') from None
            try:
                lxml.etree.XMLSchema(schema_etree).assertValid(testbed_etree)
            except lxml.etree.DocumentInvalid as e:
                raise TestbedError(f'{str(e)}({filepath})') from None
        return testbed_etree

    @property
    def name(self) -> str:
        """
        测试床名称。
        """
        return self._name
    
    @property
    def content(self) -> str:
        """
        测试床文件内容。
        """
        return self._content
    
    def xpath(self, expr: str) -> list:
        """
        通过 xpath 获取测试床文件中的内容。
        xpath 语法参考: https://lxml.de/xpathxslt.html#xpath

        :param expr: xpath 表达式。
        """
        return self._etree.xpath(expr)

    @cache
    def ssh(self, host: str, user: str, password: str, sshport: int = 22) -> SSH:
        """
        获取 SSH 连接。
        """
        return SSH(host, user, password, sshport)
