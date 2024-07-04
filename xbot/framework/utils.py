# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Utilities.
"""

import os
import re
import sys
import ctypes
import operator

import jinja2

from typing import Any, Iterator, Tuple, List, TypeVar
from functools import partial
from contextlib import contextmanager

from xbot.framework.logger import getlogger

T = TypeVar('T')

logger = getlogger(__name__)


class ColorText(object):
    """
    Colored text output.
    """

    COLORS = {
        'red': '31m',
        'green': '32m',
        'yellow': '33m'
    }

    @staticmethod
    def wrap(s, color):
        """
        Wrap string `s` with color.
        """
        code = ColorText.COLORS.get(color, None)
        if not code:
            raise ValueError('Not supported color: %s' % color)
        return '\033[%s%s\033[39m' % (code, s)


def xprint(*values, **kwargs) -> None:
    """
    Custom print function.

    :param values: values to print.
    :param color: color of the output.
    :param do_exit: if True, exit after print, default False.
    :param exit_code: exit code.
    """
    color = kwargs.pop('color', None)
    do_exit = kwargs.pop('do_exit', False)
    exit_code = kwargs.pop('exit_code', 0)
    if color:
        values = [ColorText.wrap(v, color) for v in values]
    print(*values, **kwargs)
    if do_exit:
        exit(exit_code)


printerr = partial(xprint, file=sys.stderr, color='red', do_exit=True, exit_code=1)


def render_write(template: str, outfile: str, **kwargs) -> None:
    """
    Render `template` and write to `outfile`.
    
    :param template: template file.
    :param outfile: output file.
    """
    rendered_content = ''
    with open(template, encoding='utf8') as fp:
        tpl = jinja2.Template(fp.read())
        rendered_content = tpl.render(**kwargs)
    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    with open(outfile, 'w', encoding='utf8') as fp:
        fp.write(rendered_content)


def stop_thread(thread, exc=SystemExit) -> None:
    """
    Stop a thread by raising an exception in the thread.
    
    :param thread: thread to stop.
    :param exc: exception to raise.
    :raises SystemError: if stop thread failed.
            ValueError: if invalid thread id.
    """
    r = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), ctypes.py_object(exc))
    if r == 0:
        raise ValueError("Invalid thread id '%s'" % thread.ident)
    if r != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), None)
        raise SystemError("Stop thread '%s' failed" % thread.name)


def parse_deepkey(deepkey: str, sep: str = '.') -> list:
    """
    Split deepkey by `sep`.

    :param deepkey: multi-level key.
    :param sep: separator.
    :return: list of keys.

    >>> parse_deepkey('a.b1')
    ['a', 'b1']
    >>> parse_deepkey('a.b2[0]')
    ['a', 'b2', 0]
    >>> parse_deepkey('a.b2[0].c2')
    ['a', 'b2', 0, 'c2']
    >>> parse_deepkey('a.b2[x=1].c2')
    ['a', 'b2', {'x': 1}, 'c2']
    >>> parse_deepkey('a.b2[x=1, y="z"].c2')
    ['a', 'b2', {'x': 1, 'y': 'z'}, 'c2']
    """
    keys = []
    for k in re.split(r'%s|\[' % re.escape(sep), deepkey):
        if k.endswith(']'):
            k = k[:-1]
            if k.isdigit():
                keys.append(int(k))
            else:
                try:
                    keys.append(eval(f'dict({k})'))
                except SyntaxError as e:
                    raise SyntaxError(f'Invalid expr `{k}` in deepkey `{deepkey}`: {str(e)}.')
        else:
            keys.append(k)
    return keys


def wrapstr(s: str, title: str = '') -> str:
    """
    Wrap string `s` with border.

    >>> print(wrapstr('hello world'))
    +-------------+
    | hello world |
    +-------------+
    >>> print(wrapstr('hello world\\nhello world2'))
    +--------------+
    | hello world  |
    | hello world2 |
    +--------------+
    >>> print(wrapstr('hello world', title='test'))
    +-----test----+
    | hello world |
    +-------------+

    :param s: string to wrap.
    :param title: title.
    """
    lines = s.splitlines()
    width = max(len(line) for line in lines + [title])
    return '\n'.join([
        '+' + title.center(width + 2, '-') + '+',
        *('| %s |' % line.ljust(width) for line in lines),
        '+' + '-' * (width + 2) + '+'
    ])


def ordered_walk(path: str) -> Iterator[Tuple[str, List[str], List[str]]]:
    """
    Walk through the directory in order(ascii).

    >>> import tempfile
    >>> tmpdir = tempfile.mkdtemp()
    >>> dir1 = os.path.join(tmpdir, 'dir1')
    >>> dir2 = os.path.join(tmpdir, 'dir2')
    >>> file1 = os.path.join(tmpdir, 'file1')
    >>> file2 = os.path.join(tmpdir, 'file2')
    >>> file1_1 = os.path.join(dir1, 'file1_1')
    >>> file1_2 = os.path.join(dir1, 'file1_2')
    >>> file2_1 = os.path.join(dir2, 'file2_1')
    >>> file2_2 = os.path.join(dir2, 'file2_2')
    >>> os.makedirs(os.path.join(tmpdir, 'dir1'))
    >>> os.makedirs(os.path.join(tmpdir, 'dir2'))
    >>> for file in [file1, file2, file1_1, file1_2, file2_1, file2_2]:
    ...     with open(file, 'w', encoding='utf8') as fp:
    ...         _ = fp.write('hello world')
    >>> for top, dirs, files in ordered_walk(tmpdir):
    ...     print(f'dirs: {dirs}, files: {files}')
    dirs: ['dir1', 'dir2'], files: ['file1', 'file2']
    dirs: [], files: ['file1_1', 'file1_2']
    dirs: [], files: ['file2_1', 'file2_2']

    :param path: directory path.
    :yield: (top, dirs, files)
    """
    top, dirs, files = path, [], []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_dir():
                dirs.append(entry.name)
            elif entry.is_file():
                files.append(entry.name)
    dirs.sort()
    files.sort()
    yield top, dirs, files
    for d in dirs:
        for t in ordered_walk(os.path.join(path, d)):
            yield t


def assertx(
        a: Any, 
        op: str, 
        b: Any, 
        errmsg: str = None, 
        verbose: bool = True
    ) -> None:
    """
    Assert `a` and `b` with operator `op`.

    >>> assertx(1, '==', 1)
    >>> assertx(1, '!=', 2)
    >>> assertx(1, '>', 0)
    >>> assertx(1, '>=', 1)
    >>> assertx(1, '<', 2)
    >>> assertx(1, '<=', 1)
    >>> assertx(1, 'in', [1, 2, 3])
    >>> assertx(1, 'not in', [2, 3, 4])
    >>> assertx(1, 'is', 1)
    >>> assertx(1, 'is not', 2)
    >>> assertx('abc', 'match', r'^[a-z]+$')
    >>> assertx('abc', 'not match', r'^[0-9]+$')
    >>> assertx('abc', 'search', r'[a-z]')
    >>> assertx('abc', 'not search', r'[0-9]')

    :param a: object a.
    :param op: operator.
    :param b: object b.
    :param errmsg: error message.
    :param verbose: if True, log assertion result even success.
    :raises AssertionError: if assertion failed.
            ValueError: if invalid operator.
    """
    funcs = {
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '>=': operator.ge,
        '<': operator.lt,
        '<=': operator.le,
        'in': lambda a, b: operator.contains(b, a),
        'not in': lambda a, b: not operator.contains(b, a),
        'is': operator.is_,
        'is not': operator.is_not,
        'match': lambda a, b: re.match(b, a),
        'not match': lambda a, b: not re.match(b, a),
        'search': lambda a, b: re.search(b, a),
        'not search': lambda a, b: not re.search(b, a)
    }
    if op not in funcs:
        raise ValueError('Invalid operator: %s', op)
    if not funcs[op](a, b):
        if not errmsg:
            errmsg = '%s %s %s' % (a, op, b)
        raise AssertionError(errmsg)
    if verbose:
        logger.info('AssertionOK: %s %s %s', a, op, b, stacklevel=2)


@contextmanager
def cd(path):
    """
    Change directory, support context manager(like `with`).

    :param path: directory path.
    """
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)
