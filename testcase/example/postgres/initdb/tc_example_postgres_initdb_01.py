# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

from lib.testcase import TestCase


class tc_example_postgres_initdb_01(TestCase):
    r"""
    测试用例简要描述。

    @用例名称：xxx

    @预置条件：
        1.xxxx
        2.xxxx
        3.xxxx

    @测试步骤：
        1.xxxx
        2.xxxx
        3.xxxx
        
    @预期结果：
        1.xxxx
        2.xxxx
        3.xxxx
    """

    # 用例执行最长时间，单位：分钟。
    TIMEOUT = 1
    # 用例标签。
    TAGS = ['tag1']

    def setup(self) -> None:
        """
        预置条件实现。
        """
        pg = self.testbed.xpath('/testbed/postgresql')[0]
        self.conn = self.testbed.ssh(
            pg.xpath('host/text()')[0],
            'postgres',
            pg.xpath('osusers/osuser[name="postgres"]/password/text()')[0],
            pg.xpath('sshport/text()')[0],
        )
        self.conn.setenvs({
            'PATH': pg.xpath('pghome/text()')[0] + '/bin:$PATH'
        })

    def process(self) -> None:
        """
        测试步骤实现。
        """
        self.conn.exec('initdb -D /tmp/pgdata')

    def teardown(self) -> None:
        """
        清理步骤实现。
        """
        pass
