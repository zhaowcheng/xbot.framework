# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
SSH 模块，可用于执行命令和传输文件。
"""

import os
import stat

from typing import Union, Tuple
from contextlib import contextmanager
from fabric import Connection
from invoke import Responder, UnexpectedExit
from paramiko import SFTPFile

from lib import logger
from lib.common import REs


class SSHResult(str):
    """
    带有附加信息和操作的命令回显。
    """
    def __new__(cls, s: str, cmd: str, rc: int = 0) -> str:
        """
        :param s: 命令回显。
        :param cmd: 命令。
        :param rc: 返回码。
        """
        o = str.__new__(cls, s)
        o.cmd = cmd
        o.rc = rc
        return o

    def getfield(
        self,
        key_or_row: Union[str, int],
        col: int,
        sep: str = None
    ) -> str:
        """
        从字符串中获取指定字段。

        筛选出包含 key_or_row 的第一行(为 str 类型时)，或获取 key_or_row 
        指定的行(为 int 类型时)，然后使用 sep 分割为多个字段，最后返回第 col 
        个字段，如果筛选结果为空则返回 None。

        >>> # 获取postgres主进程id
        >>> r = Result('UID     PID   CMD
        >>>             highgo   45   /opt/HighGoDB-5.6.4/bin/postgres
        >>>             highgo   51   postgres: checkpointer process
        >>>             highgo   52   postgres: writer process
        >>>             highgo   53   postgres: wal writer process')
        >>> pg_pid = r.get_field('/opt/HighgoDB', 2)
        >>> print(pg_pid)
        >>> 45

        :param key: 筛选行的关键信息或行号(从 1 开始)。
        :param col: 列号。
        :param sep: 分隔符。
        :return: 筛选结果，无结果返回 None。
        """
        matchline = ''
        lines = self.splitlines()
        if isinstance(key_or_row, str):
            for line in self.splitlines():
                if key_or_row in line:
                    matchline = line
        elif isinstance(key_or_row, int):
            matchline = lines[key_or_row-1]
        if matchline:
            fields = matchline.split(sep)
            return fields[col-1]

    def getcol(
        self,
        col: int,
        sep: str = None,
        startline: int = 1
    ) -> list:
        """
        从字符串中获取指定列。

        返回第 col 列，如果筛选结果为空则返回空列表。
		
        :param col: 列号，从 1 开始。
        :param sep: 分隔符。
        :param startline: 起始行号，从 1 开始。
        :return: 指定列的所有元素。
        """
        fields = []
        for line in self.splitlines()[startline-1:]:
            segs = line.split(sep)
            if col <= len(segs):
                fields.append(segs[col-1])
        return fields


class SSH(object):
    """
    SSH 类。
    """
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        port: int = 22,
        connect_timeout: int = 5,
        envs: dict = {}
    ) -> None:
        """
        :param host: 主机名或 IP。
        :param user: 用户名。
        :param password: 密码。
        :param port: 端口。
        :param connect_timeout: 连接超时(秒)。
        :param envs: 环境变量。
        """
        self._logger = logger.ExtraAdapter(logger.get_logger())
        self._logger.extra = f'{user}@{host}:{port}'
        self._logger.info('Connecting...')
        self._conn = Connection(host=host, user=user, port=port, 
                                connect_timeout=connect_timeout,
                                connect_kwargs={'password': str(password)},
                                inline_ssh_env=True)
        self._conn.open()
        self._cwd = ''
        self._envs = envs
    
    def close(self) -> None:
        """
        关闭连接。
        """
        self._conn.close()

    def setenvs(self, envs: dict) -> None:
        """
        设置环境变量。
        """
        self._envs.update(envs)

    @contextmanager
    def cd(self, path) -> None:
        """
        切换工作路径。

        >>> with cd('/my/workdir'):
        ...     exec('pwd')
        ...
        /my/workdir
        """
        r = self._conn.run(f'cd {path}', hide=True, env=self._envs)
        if path == '-':
            self._cwd = r.stdout
        else:
            self._cwd = path
        try:
            yield
        finally:
            self._cwd = ''
        
    def exec(
        self,
        command: str,
        timeout: int = 30,
        prompts: dict = {},
        pty=True,
        fail=True
    ) -> SSHResult:
        """
        执行命令。

        >>> exec('uname -s')
        Linux
        >>> exec('sudo whoami', prompts={'password:', 'mypwd'})
        root

        :param command: 命令。
        :param timeout: 命令超时(秒)。
        :param prompts: 用于交互式命令的提示及响应。
        :param pty: 是否使用 pty。
        :param fail: 命令执行失败时是否抛出异常。
        :return: 命令输出。
        """
        if self._cwd:
            command = f'cd {self._cwd} && {command}'
        extra = {'result': {}}
        self._logger.info(f'Command: {command}', extra=extra)
        watchers = [Responder(k, v + '\n') for k, v in prompts.items()]
        try:
            result = self._conn.run(command, timeout=timeout, 
                                    watchers=watchers, pty=pty, 
                                    hide=True, env=self._envs)
        except UnexpectedExit as e:
            if fail:
                raise e from None
            else:
                stdout = REs.ANSI_ESCAPE.sub('', e.streams_for_display()[0])
                sshres = SSHResult(stdout, e.result.exited, command)
                extra['result']['content'] = sshres
                return sshres
        stdout = REs.ANSI_ESCAPE.sub('', result.stdout.strip())
        sshres = SSHResult(stdout, result.exited, command)
        extra['result']['content'] = sshres
        return sshres
    
    def sudo(self, command: str, **kwargs) -> str:
        """
        sudo 方式执行命令，参数及返回值与 exec 一致。
        """
        command = 'sudo ' + command
        kwargs['prompts'] = {
            r'\[sudo\] password': self._conn.connect_kwargs['password']
        }
        return self.exec(command, **kwargs)
    
    def getfile(self, rfile: str, ldir: str) -> None:
        """
        下载文件。

        >>> getfile('/tmp/myfile', '/home')  # /home/myfile
        >>> getfile('/tmp/myfile', 'D:\\')  # D:\\myfile
        
        :param rfile: 远端文件路径。
        :param ldir: 本地目录。
        """
        ldir = os.path.join(ldir, '')
        self._logger.info(f'Getting file {ldir} <= {rfile}')
        filename = self.basename(rfile)
        lfile = os.path.join(ldir, filename)
        self._conn.sftp().get(rfile, lfile)

    def putfile(self, lfile: str, rdir: str) -> None:
        """
        上传文件。

        >>> putfile('/home/myfile', '/tmp')  # /tmp/myfile
        >>> putfile('D:\\myfile', '/tmp')  # /tmp/myfile

        :param lfile: 本地文件路径。
        :param rdir: 远端目录。
        """
        rdir = self.join(rdir, '')
        self._logger.info(f'Putting file {lfile} => {rdir}')
        filename = os.path.basename(lfile)
        rfile = self.join(rdir, filename)
        self._conn.sftp().put(lfile, rfile)
            
    def getdir(self, rdir: str, ldir: str) -> None:
        """
        下载目录。
        
        >>> getdir('/tmp/mydir', '/home')  # /home/mydir
        >>> getdir('/tmp/mydir', 'D:\\')  # D:\\mydir

        :param rdir: 远端目录。
        :param ldir: 本地目录。
        """
        rdir = self.normpath(rdir)
        ldir = os.path.join(ldir, '')
        self._logger.info(f'Getting dir {ldir} <= {rdir}')
        for top, dirs, files in self.walk(rdir):
            basename = self.basename(top)
            ldir = os.path.join(ldir, basename)
            if not os.path.exists(ldir):
                os.makedirs(ldir)
            for f in files:
                r = self.join(top, f)
                l = os.path.join(ldir, f)
                self._conn.sftp().get(r, l)
            for d in dirs:
                l = os.path.join(ldir, d)
                if not os.path.exists(l):
                    os.makedirs(l)

    def putdir(self, ldir: str, rdir: str) -> None:
        """
        上传目录。

        >>> putdir('/tmp/mydir', '/home')  # /home/mydir
        >>> putdir('D:\\mydir', '/home')  # /home/mydir

        :param ldir: 本地目录。
        :param rdir: 远端目录。
        """
        ldir = os.path.normpath(ldir)
        rdir = self.join(rdir, '')
        self._logger.info(f'Putting dir {ldir} => {rdir}')
        for top, dirs, files in os.walk(os.path.normpath(ldir)):
            basename = os.path.basename(top)
            rdir = self.join(rdir, basename)
            if not self.exists(rdir):
                self.makedirs(rdir)
            for f in files:
                l = os.path.join(top, f)
                r = self.join(rdir, f)
                self._conn.sftp().put(l, r)
            for d in dirs:
                r = self.join(rdir, d)
                if not self.exists(r):
                    self.makedirs(r)

    def join(self, *paths: str) -> str:
        """
        拼接远端路径，类似于 os.path.join()。
        """
        paths = [p.rstrip('/') for p in paths]
        return '/'.join(paths)

    def normpath(self, path: str) -> str:
        """
        正常化远端路径，类似于 os.path.normpath()。
        """
        segs = [s.strip('/') for s in path.split('/')]
        path = self.join(*segs)
        return path.rstrip('/')

    def basename(self, path: str) -> str:
        """
        获取远端路径的末尾字段，类似于 os.path.basename()。
        """
        return path.rsplit('/', 1)[-1]

    def exists(self, path: str) -> str:
        """
        判断远端路径是否存在，类似于 os.path.exists()。
        """
        try:
            self._conn.sftp().stat(path)
            return True
        except FileNotFoundError:
            return False

    def walk(self, path: str):
        """
        递归远端目录，类似于 os.walk()。
        """
        dirs, files =  [], []
        for a in self._conn.sftp().listdir_attr(path):
            if stat.S_ISDIR(a.st_mode):
                dirs.append(a.filename)
            else:
                files.append(a.filename)
        yield path, dirs, files

        for d in dirs:
            for w in self.walk(self.join(path, d)):
                yield w

    def makedirs(self, path: str) -> str:
        """
        在远端创建目录，类似于 os.makedirs()。
        """
        self._logger.info('Makedirs %s' % path)
        curpath = '/'
        for p in path.split('/'):
            curpath = self.join(curpath, p)
            if not self.exists(curpath):
                self._conn.sftp().mkdir(curpath)

    @contextmanager
    def openfile(self, filepath: str, mode: str = 'r') -> SFTPFile:
        """
        打开远端文件，用法与内建函数 open 相同。
        """
        self._logger.info('Open %s with mode=%s' % (filepath, mode))
        f = self._conn.sftp().open(filepath, mode)
        try:
            yield f
        finally:
            f.close()
