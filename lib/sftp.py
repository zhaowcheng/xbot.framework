# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
SFTP module
"""


import os
import stat
import paramiko

from lib import logger


class SFTP(object):
    """
    SFTP Class.
    """
    def __init__(self):
        self._sftpclient = None
        self._logger = logger.ExtraAdapter(logger.get_logger())

    def connect(
        self,
        host: str,
        user: str,
        password: str,
        port: int = 22
    ) -> None:
        """
        SFTP to `host:port` with `user` and `password`.
        """
        self._logger.extra = f'sftp://{user}@{host}:{port}'
        self._logger.info('Connecting...')
        t = paramiko.Transport((host, port))
        t.connect(username=user, password=password)
        self._sftpclient = paramiko.SFTPClient.from_transport(t)

    def close(self) -> None:
        """
        Close the connection.
        """
        self._sftpclient.close()

    @property
    def closed(self) -> bool:
        """
        Whether the connection is closed.
        """
        return self._sftpclient.sock.closed

    def getfile(self, rfile: str, ldir: str) -> None:
        """
        Get `rfile` from SFTP server into `ldir`.
        
        :param rfile: remote file.
        :param ldir: local dir.

        :examples:
            >>> getfile('/tmp/myfile', '/home')  # /home/myfile
            >>> getfile('/tmp/myfile', 'D:\\')  # D:\\myfile
        """
        ldir = os.path.join(ldir, '')
        self._logger.info(f'Getting file {ldir} <= {rfile}')
        filename = self.basename(rfile)
        lfile = os.path.join(ldir, filename)
        self._sftpclient.get(rfile, lfile)

    def putfile(self, lfile: str, rdir: str) -> None:
        """
        Put `lfile` into the `rdir` of SFTP server.

        :param lfile: local file.
        :param rdir: remote dir.

        :examples:
            >>> putfile('/home/myfile', '/tmp')  # /tmp/myfile
            >>> putfile('D:\\myfile', '/tmp')  # /tmp/myfile
        """
        rdir = self.join(rdir, '')
        self._logger.info(f'Putting file {lfile} => {rdir}')
        filename = os.path.basename(lfile)
        rfile = self.join(rdir, filename)
        self._sftpclient.put(lfile, rfile)
            
    def getdir(self, rdir: str, ldir: str) -> None:
        """
        Get `rdir` from SFTP server into `ldir`.
        
        :param rdir: remote dir.
        :param ldir: local dir.

        :examples:
            >>> getdir('/tmp/mydir', '/home')  # /home/mydir
            >>> getdir('/tmp/mydir', 'D:\\')  # D:\\mydir
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
                self._sftpclient.get(r, l)
            for d in dirs:
                l = os.path.join(ldir, d)
                if not os.path.exists(l):
                    os.makedirs(l)

    def putdir(self, ldir: str, rdir: str) -> None:
        """
        Put `ldir` into the `rdir` of SFTP server.

        :param ldir: local dir.
        :param rdir: remote dir.

        :examples:
            >>> putdir('/tmp/mydir', '/home')  # /home/mydir
            >>> putdir('D:\\mydir', '/home')  # /home/mydir
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
                self._sftpclient.put(l, r)
            for d in dirs:
                r = self.join(rdir, d)
                if not self.exists(r):
                    self.makedirs(r)

    def join(self, *paths):
        """
        Similar to os.path.join().
        """
        paths = [p.rstrip('/') for p in paths]
        return '/'.join(paths)

    def normpath(self, path):
        """
        Similar to os.path.normpath().
        """
        segs = [s.strip('/') for s in path.split('/')]
        path = self.join(*segs)
        return path.rstrip('/')

    def basename(self, path):
        """
        Similar to os.path.basename().
        """
        return path.rsplit('/', 1)[-1]

    def exists(self, path):
        """
        Similar to os.path.exists().
        """
        try:
            self._sftpclient.stat(path)
            return True
        except FileNotFoundError:
            return False

    def walk(self, path):
        """
        Similar to os.walk().
        """
        dirs, files =  [], []
        for a in self._sftpclient.listdir_attr(path):
            if stat.S_ISDIR(a.st_mode):
                dirs.append(a.filename)
            else:
                files.append(a.filename)
        yield path, dirs, files

        for d in dirs:
            for w in self.walk(self.join(path, d)):
                yield w

    def makedirs(self, path):
        """
        Similar to os.makedirs().
        """
        self._logger.info('Makedirs %s' % path)
        curpath = '/'
        for p in path.split('/'):
            curpath = self.join(curpath, p)
            if not self.exists(curpath):
                self._sftpclient.mkdir(curpath)

    def open(self, filepath, mode='r'):
        """
        Similar to builtin open().
        """
        self._logger.info('Open %s with mode=%s' % (filepath, mode))
        return self._sftpclient.open(filepath, mode)
