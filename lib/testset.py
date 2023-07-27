# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试套相关模块。
"""

import os
import typing
import lxml.etree

from io import StringIO
from lib import common


SCHEMA = """\
<!-- Created with Liquid Technologies Online Tools 1.0 (https://www.liquid-technologies.com) -->
<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="testset">
    <xs:complexType>
      <xs:sequence>
        <xs:element maxOccurs="unbounded" name="path">
          <xs:complexType>
            <xs:simpleContent>
              <xs:extension base="xs:string">
                <xs:attribute name="tags" type="xs:string" use="required" />
              </xs:extension>
            </xs:simpleContent>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
"""


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
        self.__etree = self.__parse(filepath)

    def __parse(self, filepath: str) -> typing.Any:
        """
        解析并验证测试套文件。
        """
        testset_etree = lxml.etree.parse(filepath)
        testset_etree_root = lxml.etree.parse(filepath).getroot()
        if testset_etree_root.tag != 'testset':
            raise TestsetError(
                'The tag of the root element must be `testset`, ' \
                f'but now is `{testset_etree_root.tag}`.'
            )
        schema_etree = lxml.etree.fromstring(SCHEMA)
        try:
            lxml.etree.XMLSchema(schema_etree).assertValid(testset_etree)
        except lxml.etree.DocumentInvalid as e:
            raise TestsetError(f'{str(e)}({filepath})') from None
        return testset_etree
