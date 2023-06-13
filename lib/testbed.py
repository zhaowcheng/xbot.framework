# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Test environment management.
"""

import os
import typing
import lxml.etree

from lib import common
from lib.error import TestbedError, TestbedSchemaError


class TestBed(object):
    """
    Testbed class.
    """
    def __init__(self, filepath: str) -> None:
        """
        :param filepath: testbed filepath.
        """
        self.__etree = self.__parse(filepath)
        with open(filepath) as f:
            self.__content = f.read()

    def __parse(self, filepath: str) -> typing.Any:
        """
        parse and validate the testbed file.
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
    def content(self) -> str:
        """
        Testbed file content.
        """
        return self.__content
    
    def xpath(self, expr: str) -> list:
        """
        Get elements by xpath.
        reference: https://lxml.de/xpathxslt.html#xpath

        :param expr: xpath expression
        """
        return self.__etree.xpath(expr)
