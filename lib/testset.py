# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
测试套相关模块。
"""

import os
import textwrap
import lxml.etree

from functools import cached_property
from typing import Any, List
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

    SCHEMA = textwrap.dedent("""\
        <!-- Created with Liquid Technologies Online Tools 1.0 (https://www.liquid-technologies.com/online-xml-to-xsd-converter) -->
        <xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified"
          xmlns:xs="http://www.w3.org/2001/XMLSchema">
          <xs:element name="testset">
            <xs:complexType>
              <xs:sequence>
                <xs:element name="tags">
                  <xs:complexType>
                    <xs:sequence>
                      <xs:element maxOccurs="unbounded" minOccurs="0" name="tag" type="xs:string" />
                    </xs:sequence>
                  </xs:complexType>
                </xs:element>
                <xs:element name="paths">
                  <xs:complexType>
                    <xs:sequence>
                      <xs:element maxOccurs="unbounded" name="path" type="xs:string" />
                    </xs:sequence>
                  </xs:complexType>
                </xs:element>
              </xs:sequence>
            </xs:complexType>
          </xs:element>
        </xs:schema>
    """)

    def __init__(self, filepath: str) -> None:
        """
        :param filepath: 测试套文件路径。
        """
        self._etree = self._parse(filepath)

    def _parse(self, filepath: str) -> Any:
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
        schema_etree = lxml.etree.fromstring(self.SCHEMA)
        try:
            lxml.etree.XMLSchema(schema_etree).assertValid(testset_etree)
        except lxml.etree.DocumentInvalid as e:
            raise TestsetError(f'{str(e)}({filepath})') from None
        return testset_etree

    @cached_property
    def tags(self) -> List[str]:
        """
        测试套中的标签。
        """
        return self._etree.xpath('/testset/tags/tag/text()')

    @cached_property
    def paths(self) -> List[str]:
        """
        测试套中的路径。
        """
        paths = []
        for p in self._etree.xpath('/testset/paths/path/text()'):
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
