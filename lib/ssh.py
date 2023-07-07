# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
SSH module.
"""

import os
import stat

from contextlib import contextmanager
from fabric import Connection
from invoke import Responder
from paramiko import SFTPFile

from lib import logger
from lib import common


class Result(str):
    """
    Shell command result with extra attributes and methods.
    """
    def getfield(
        self,
        key: str,
        col: int,
        sep: str = None
    ) -> str:
        """
        Get the specified field from result.

        >>> r = Result('UID     PID   CMD
        >>>             highgo   45   /opt/HighGoDB-5.6.4/bin/postgres
        >>>             highgo   51   postgres: checkpointer process
        >>>             highgo   52   postgres: writer process
        >>>             highgo   53   postgres: wal writer process')
        >>> pg_pid = r.getfield('/opt/HighgoDB', 2)
        >>> print(pg_pid)
        >>> 45

        :param key: keyword to filter row.
        :param col: column number.
        :param sep: separator.
        :return: filtered field.
        """
        for line in self.splitlines():
            if key in line:
                fields = line.split(sep)
                if col <= len(fields):
                    return fields[col-1]

    def getcol(
        self,
        col: int,
        sep: str = None,
        start: int = 1
    ) -> list:
        """
        Get all fields of the specified column.

        >>> r = Result('UID     PID   CMD
        >>>             highgo   45   /opt/HighGoDB-5.6.4/bin/postgres
        >>>             highgo   51   postgres: checkpointer process
        >>>             highgo   52   postgres: writer process
        >>>             highgo   53   postgres: wal writer process')
        >>> pids = r.getcol(2, start=2)
        >>> print(pids)
        >>> ['45', '51', '52', '53']

        :param col: column number, start from 1.
        :param sep: separator.
        :param start: start line number.
        :return: all fields of the specified column.
        """
        fields = []
        for line in self.splitlines()[start-1:]:
            segs = line.split(sep)
            if col <= len(segs):
                fields.append(segs[col-1])
        return fields


class SSH(object):
    """
    SSH Class.
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
        :param envs: shell environments.
        """
        self.__conn = Connection(host=host, user=user, port=port, 
                                 connect_kwargs={'password': password},
                                 connect_timeout=connect_timeout,
                                 inline_ssh_env=True)
        self.__conn.open()
        self.__sftp = self.__conn.sftp()
        self.__envs = envs
        self.__cwd = ''
        self.__logger = logger.ExtraAdapter(logger.get_logger())
        self.__logger.extra = f'ssh://{user}@{host}:{port}'

    def close(self) -> None:
        """
        Close the connection.
        """
        self.__conn.close()

    def setenv(self, name: str, value: str) -> None:
        """
        Set shell environment.
        """
        self.__envs[name] = value

    def delenv(self, name: str) -> None:
        """
        Delete shell environment.
        """
        self.__envs.pop(name, None)

    @contextmanager
    def cd(self, path) -> None:
        """
        Shell `cd` command.

        >>> with cd('/my/workdir'):
        ...     run('pwd')
        ...
        /my/workdir
        """
        r = self.__conn.run(f'cd {path}', hide=True, env=self.__envs)
        if path == '-':
            self.__cwd = r.stdout
        else:
            self.__cwd = path
        try:
            yield
        finally:
            self.__cwd = ''
        
    def exec(
        self,
        command: str,
        timeout: int = 10,
        prompts: dict = {},
        pty=True
    ) -> Result:
        """
        Execute a command on the SSH server.

        >>> exec('uname -s')
        Linux
        >>> exec('sudo whoami', prompts={'password:', 'mypwd'})
        root

        :param prompts: for interactive command.
        :return: command output.
        """
        if self.__cwd:
            command = f'cd {self.__cwd} && {command}'
        extra = {'result': {}}
        self.__logger.debug(f'Command: {command}', extra=extra)
        watchers = [Responder(k, v + '\n') for k, v in prompts.items()]
        result = self.__conn.run(command, timeout=timeout, 
                                 watchers=watchers, pty=pty, 
                                 hide=True, env=self.__envs)
        stdout = common.REs.ANSI_ESCAPE.sub('', result.stdout.strip())
        extra['result']['content'] = stdout
        return Result(stdout)
    
    def sudo(self, command: str, **kwargs) -> str:
        """
        Same to shell sudo.

        >>> sudo('whoami')
        root

        :param kwargs: arguments passed to `exec`.
        :return: command output.
        """
        command = 'sudo ' + command
        kwargs['prompts'] = {
            r'\[sudo\] password': self.__conn.connect_kwargs['password']
        }
        result = self.exec(command, **kwargs)
        return Result('\n'.join(result.splitlines()[1:]))
    
    def getfile(self, rfile: str, ldir: str) -> None:
        """
        Get `rfile` from SFTP server into `ldir`.

        >>> getfile('/tmp/myfile', '/home')  # /home/myfile
        >>> getfile('/tmp/myfile', 'D:\\')  # D:\\myfile
        
        :param rfile: remote file.
        :param ldir: local dir.
        """
        ldir = os.path.join(ldir, '')
        self.__logger.info(f'Getting file {ldir} <= {rfile}')
        filename = self.basename(rfile)
        lfile = os.path.join(ldir, filename)
        self.__sftp.get(rfile, lfile)

    def putfile(self, lfile: str, rdir: str) -> None:
        """
        Put `lfile` into the `rdir` of SFTP server.

        >>> putfile('/home/myfile', '/tmp')  # /tmp/myfile
        >>> putfile('D:\\myfile', '/tmp')  # /tmp/myfile

        :param lfile: local file.
        :param rdir: remote dir.
        """
        rdir = self.join(rdir, '')
        self.__logger.info(f'Putting file {lfile} => {rdir}')
        filename = os.path.basename(lfile)
        rfile = self.join(rdir, filename)
        self.__sftp.put(lfile, rfile)
            
    def getdir(self, rdir: str, ldir: str) -> None:
        """
        Get `rdir` from SFTP server into `ldir`.

        >>> getdir('/tmp/mydir', '/home')  # /home/mydir
        >>> getdir('/tmp/mydir', 'D:\\')  # D:\\mydir
        
        :param rdir: remote dir.
        :param ldir: local dir.
        """
        rdir = self.normpath(rdir)
        ldir = os.path.join(ldir, '')
        self.__logger.info(f'Getting dir {ldir} <= {rdir}')
        for top, dirs, files in self.walk(rdir):
            basename = self.basename(top)
            ldir = os.path.join(ldir, basename)
            if not os.path.exists(ldir):
                os.makedirs(ldir)
            for f in files:
                r = self.join(top, f)
                l = os.path.join(ldir, f)
                self.__sftp.get(r, l)
            for d in dirs:
                l = os.path.join(ldir, d)
                if not os.path.exists(l):
                    os.makedirs(l)

    def putdir(self, ldir: str, rdir: str) -> None:
        """
        Put `ldir` into the `rdir` of SFTP server.

        >>> putdir('/tmp/mydir', '/home')  # /home/mydir
        >>> putdir('D:\\mydir', '/home')  # /home/mydir

        :param ldir: local dir.
        :param rdir: remote dir.
        """
        ldir = os.path.normpath(ldir)
        rdir = self.join(rdir, '')
        self.__logger.info(f'Putting dir {ldir} => {rdir}')
        for top, dirs, files in os.walk(os.path.normpath(ldir)):
            basename = os.path.basename(top)
            rdir = self.join(rdir, basename)
            if not self.exists(rdir):
                self.makedirs(rdir)
            for f in files:
                l = os.path.join(top, f)
                r = self.join(rdir, f)
                self.__sftp.put(l, r)
            for d in dirs:
                r = self.join(rdir, d)
                if not self.exists(r):
                    self.makedirs(r)

    def join(self, *paths: str) -> str:
        """
        Similar to os.path.join().
        """
        paths = [p.rstrip('/') for p in paths]
        return '/'.join(paths)

    def normpath(self, path: str) -> str:
        """
        Similar to os.path.normpath().
        """
        segs = [s.strip('/') for s in path.split('/')]
        path = self.join(*segs)
        return path.rstrip('/')

    def basename(self, path: str) -> str:
        """
        Similar to os.path.basename().
        """
        return path.rsplit('/', 1)[-1]

    def exists(self, path: str) -> str:
        """
        Similar to os.path.exists().
        """
        try:
            self.__sftp.stat(path)
            return True
        except FileNotFoundError:
            return False

    def walk(self, path: str):
        """
        Similar to os.walk().
        """
        dirs, files =  [], []
        for a in self.__sftp.listdir_attr(path):
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
        Similar to os.makedirs().
        """
        self.__logger.info('Makedirs %s' % path)
        curpath = '/'
        for p in path.split('/'):
            curpath = self.join(curpath, p)
            if not self.exists(curpath):
                self.__sftp.mkdir(curpath)

    @contextmanager
    def openfile(self, filepath: str, mode: str = 'r') -> SFTPFile:
        """
        Similar to builtin open().
        """
        self.__logger.debug('Open %s with mode=%s' % (filepath, mode))
        f = self.__sftp.open(filepath, mode)
        try:
            yield f
        finally:
            f.close()
