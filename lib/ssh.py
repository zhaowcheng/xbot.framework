# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
SSH module.
"""

import inspect
import threading
import time
import re
import random
import string

from typing import Tuple, Any
from datetime import datetime
from paramiko import SSHClient, AutoAddPolicy, Channel

from lib.error import ShellError

class SSH(object):
    """
    SSH Class.
    """

    PS1 = '[sh@xbot]$ '

    def __init__(self, shenvs: dict = {}):
        """
        :param shenvs: shell environment variables for exec().
            PS1 defaults to SSH.PS1 and cannot be changed.
            LANG defaults to en_US.UTF-8 and cannot be changed.
            LANGUAGE defaults to en_US.UTF-8 and cannot be changed.
        """
        self._sshclient = SSHClient()
        self._sshclient.set_missing_host_key_policy(AutoAddPolicy())
        self._shells = {}
        self._shenvs = shenvs
        self._shenvs.update(PS1=SSH.PS1, 
                            LANG='en_US.UTF-8', 
                            LANGUAGE='en_US.UTF-8')
        self._profile = None

    def connect(
        self,
        host: str,
        user: str,
        password: str,
        port: int = 22
    ) -> None:
        """
        SSH to `host:port` with `user` and `password`.
        """
        self._sshclient.connect(host, port, user, password)
        self._profile = self._mkprofile()

    def close(self) -> None:
        """
        Close the connection.
        """
        for name in self._shells:
            self._shells.pop(name).close()
        self._sshclient.close()

    @property
    def closed(self) -> bool:
        """
        Whether the connection is closed.
        """
        transport = self._sshclient.get_transport()
        if transport and transport.is_active():
            return False
        return True

    def close_shell(self, name: str) -> None:
        """
        Close the sepecified shell by name.
        """
        self._shells.pop(name).close()

    def shell_names(self) -> Tuple[str]:
        """
        Return all cached shell names.
        """
        return tuple(self._shells.keys())

    def exec(
        self,
        cmd: str,
        expect: str = '0',
        timeout: int = 10
    ) -> str:
        """
        Execute a command on the SSH server.

        :param cmd: the command to be executed.
        :param expect: expected result of command execution.
            '0': expect the command to execute successfully.
            '' : do not check the result of command execution.
            's': expect the str 's' to appear in the result.
        :param timeout: command timeout (seconds).
        :return: the result of command execution.

        :raises: `.ShellError` -- if the result is not as expected.

        :examples:
            >>> exec('cd /home')  # successful
            >>> exec('cd /errpath')  # ShellError
            >>> exec('cd /errpath', expect='')  # no error
            >>> exec('mkdir d1 d2')
            >>> exec('rm -ri d1 d2', expect="remove directory 'd1'?")
            >>> exec('y', expect="remove directory 'd2'?")  # d1 deleted
            >>> exec('y')  # d2 deleted
        """
        data = f'{cmd}\necho $?' if expect == '0' else cmd
        caller = inspect.stack()[1]
        callermod = inspect.getmodulename(caller.filename)
        threadname = threading.current_thread().name
        shname = f'{callermod}-{threadname}'
        if shname not in self._shells:
            shell = self._sshclient.invoke_shell('builtin_ansi', 999, 999)
            shell.set_name(shname)
            self._shells[shname] = shell
            data = f'source ${self._profile}\n${data}'
        shell = self._shells[shname]
        shell.send(data + '\r')
        result = _Result(self.PS1, cmd, expect)
        stime = datetime.now()
        while (datetime.now() - stime).seconds < timeout:
            if shell.recv_ready():
                result.appendrs(shell.recv(1024))
                if result.finished:
                    return result.purers
            time.sleep(0.01)
        else:
            if expect in ('0', ''):
                prefix = 'Command timeout:'
            else:
                prefix = f"No '{expect}' found:"
            msg = f'{prefix}\n{self.PS1}{cmd}\n{result.purers}'
            raise ShellError(msg) from None

    def _mkprofile(self) -> str:
        """
        Create a profile for shell environments.
        """
        rdmchrs = random.choices(string.ascii_letters, k=10)
        profile = '/tmp/' + ''.join(rdmchrs)
        sftp = self._sshclient.open_sftp()
        with sftp.open(profile, 'w+') as fp:
            for k, v in self._shenvs.items():
                fp.write(f'export {k}={v}\n')
        return profile


class _Result(object):
    """
    Result of shell command.
    """

    def __init__(
        self,
        ps1: str,
        cmd: str,
        expect: str,
    ):
        """
        :param ps1: shell PS1.
        :param cmd: shell command.
        :param expect: expected result.
        """
        self._ps1 = ps1
        self._cmd = cmd
        self._expect = expect
        self._rs = ''  # return str of cmd.
        self._rc = ''  # return code of cmd.
        self._purers = ''  # return str that has removed redundant lines.
        self._start = None  # start line number of purers in the rs.
        self._end = None  # end line number of purers in the rs.

    @property
    def rc(self) -> str:
        """
        Return code.
        """
        return self._rc

    @property
    def rs(self) -> str:
        """
        Return str.
        """
        return self._rs

    @property
    def purers(self) -> str:
        """
        Pure return str.
        """
        return self._purers

    @property
    def finished(self) -> bool:
        """
        Whether the command execution is finished.
        """
        if self._expect == '0':
            return self._rc != ''
        elif self._expect == '':
            return self._end != None
        else:
            return self._expect in self._purers

    def appendrs(self, s: str) -> None:
        """
        Append content to return str.
        """
        self._rs += s
        self._start, self._end = self._locate_purers()
        self._purers = '\n'.join(
            self._rs.splitlines()[self._start:self._end]).strip()
        if self._expect == '0':
            self._rc = self._getrc()

    def _getrc(self) -> str:
        """
        Get return code from return str.
        """
        if self._end == None:
            return ''
        lines = self._rs.splitlines()[self._end:]
        if len(lines) < 3:
            return ''
        ps1line = re.compile(f'.*?{self._ps1}.*')
        if not ps1line.match(lines[-1]):
            return ''
        rc = lines[-2]
        if not re.match(r'\d+', rc):
            return ''
        return rc
        
    def _locate_purers(self):
        """
        Locate the start and end line number of purers.
        """
        start, end = None, None
        ps1line = re.compile(f'.*?{self._ps1}.*')
        for i, line in enumerate(self._rs.splitlines()):
            if (start is None) and (line == self._cmd):
                start = i
                continue
            if ps1line.match(line) and \
                    line.endswith(self._cmd) and \
                    self._cmd.strip() != '':
                start = i
                continue
            if ps1line.match(line):
                if (' ' in self._cmd.strip()) and (start is None):
                    continue
                else:
                    end = i
                    break
        return start, end