# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
SSH module.
"""

import paramiko

class SSH(object):

    def __init__(self):
        self._sshclient = paramiko.SSHClient()
        self._sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(
        self,
        host: str,
        user: str,
        password: str,
        port: int = 22
    ) -> None:
        """
        SSH connect to host with (user, password).
        """