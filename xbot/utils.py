# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
实用函数。
"""

import os
import re
import sys
import ctypes
import operator
import socket

import jinja2

from typing import Any, Iterator, Tuple, List
from functools import reduce, partial
from contextlib import contextmanager

from xbot.logger import getlogger


logger = getlogger('util')


class ColorText(object):
    """
    给终端字符添加 ascii 颜色码。
    """

    COLORS = {
        'red': '31m',
        'green': '32m',
        'yellow': '33m'
    }

    @staticmethod
    def wrap(s, color):
        """
        给字符串 `s` 添加颜色。
        """
        code = ColorText.COLORS.get(color, None)
        if not code:
            raise ValueError('Not supported color: %s' % color)
        return '\033[%s%s\033[39m' % (code, s)


def xprint(*values, **kwargs) -> None:
    """
    专用 print 函数。

    :param values: 待打印的值。
    :param color: 字符颜色。
    :param do_exit: 打印后是否退出程序，默认 False。
    :param exit_code: 退出码，默认 0。
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
    渲染 HTML 模板 `template` 并输出到 `outfile`。
    
    :param template: HTML 模板文件。
    :param outfile: 输出文件。
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
    通过让线程抛出异常来结束线程。
    
    :param thread: 线程实例。
    :param exc: 抛出的异常类。
    :raises SystemError: 如果停止线程失败。
            ValueError: 如果线程 ident 无效。
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
    把路径 `deepkey` 按照 `sep` 分隔为列表，其中数字会转为 int 类型。

    >>> parse_deepkey('a.b1')
    ['a', 'b1']
    >>> parse_deepkey('a.b2[0]')
    ['a', 'b2', 0]
    >>> parse_deepkey('a.b2[0].c2')
    ['a', 'b2', 0, 'c2']

    :param deepkey: 路径。
    :param sep: 分隔符
    :return: 分隔后的路径列表。
    """
    keys = []
    for k in re.split(r'%s|\[' % re.escape(sep), deepkey):
        if k.endswith(']') and k[:-1].isdigit():
            keys.append(int(k[:-1]))
        else:
            keys.append(k)
    return keys


def deepget(obj, deepkey: str, sep: str = '.') -> Any:
    """
    深度获取 `obj` 中的元素的值。

    >>> d = {
    ...     'a': {
    ...         'b1': 'c',
    ...         'b2': [1, 2, 3]
    ...      }
    ... }
    >>> deepget(d, 'a.b1')
    'c'
    >>> deepget(d, 'a.b2[0]')
    1

    :param obj: 被获取对象。
    :param deepkey: 元素路径。
    :param sep: 路径分隔符。
    :return: 获取到的值。
    """
    keys = parse_deepkey(deepkey, sep)
    return reduce(operator.getitem, keys, obj)


def deepset(obj: Any, deepkey: str, value: Any, sep: str = '.') -> None:
    """
    深度设置 `obj` 中的元素的值。
    如果路径不存在会自动创建（路径中包含索引的情况除外，如 a.b[0]）。

    >>> d = {
    ...     'a': {
    ...         'b1': 'c',
    ...         'b2': [1, 2, 3]
    ...      }
    ... }
    >>> deepset(d, 'a.b1', 'd')
    >>> d
    {'a': {'b1': 'd', 'b2': [1, 2, 3]}}
    >>> deepset(d, 'a.b2[0]', '-1')
    >>> d
    {'a': {'b1': 'd', 'b2': ['-1', 2, 3]}}
    >>> deepset(d, 'i.j', 'x')
    >>> d
    {'a': {'b1': 'd', 'b2': ['-1', 2, 3]}, 'i': {'j': 'x'}}

    :param obj: 被设置对象。.
    :param deepkey: 元素路径。
    :param value: 被设置的值
    :param sep: 路径分隔符。
    """
    keys = parse_deepkey(deepkey, sep)
    for k in keys[:-1]:
        try:
            obj = operator.getitem(obj, k)
        except KeyError:
            obj[k] = {}
            obj = obj[k]
    operator.setitem(obj, keys[-1], value)


def ip_reachable(ip: str) -> bool:
    """
    检查 IP 地址是否可达

    >>> ip_reachable('127.0.0.1')
    True
    >>> ip_reachable('128.0.0.1')
    False

    :param ip: IP 地址。
    :return: 可达返回 True，否则 False。
    """
    try:
        conn = socket.create_connection((ip, 22), 0.1)
        conn.close()
        return True
    except ConnectionRefusedError:
        return True
    except:
        return False


def port_opened(ip: str, port: int) -> bool:
    """
    检查端口是否开放。

    :param ip: IP 地址
    :param port: 端口号
    :return: 开放返回 True，否则 False。
    """
    try:
        conn = socket.create_connection((ip, port), 0.1)
        conn.close()
        return True
    except:
        return False
    

def wrapstr(s: str, title: str = '') -> str:
    """
    使用字符边框包裹字符串 `s`。

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

    :param s: 字符串。
    :param title: 标题。
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
    按名称顺序对目录进行遍历。

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

    :param path: 被遍历路径。
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
    断言函数。

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

    :param a: 操作对象 a。
    :param op: 操作符。
    :param b: 操作对象 b。
    :param errmsg: 断言失败时的错误消息，如果未制定则自动生成。
    :param verbose: 如果为 True，断言成功时也打印打印一条日志。
    :raises AssertionError: 如果断言失败。
            ValueError: 不支持的操作符。
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
    切换当前工作目录。（支持 with 语句）

    :param path: 目标目录。
    """
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)
