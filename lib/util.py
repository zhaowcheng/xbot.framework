# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
实用函数。
"""

import os
import jinja2
import functools
import ctypes

from threading import Thread


class ColorText(object):
    """
    终端彩色文本。
    """

    COLORS = {
        'red': '31m',
        'green': '32m',
        'yellow': '33m'
    }

    @staticmethod
    def wrap(s: str, color: str) -> str:
        """
        给字符串 `s` 添加颜色 `color`。
        """
        code = ColorText.COLORS.get(color, None)
        if not code:
            raise ValueError(f'Not supported color: {color}')
        return f'\033[{code}{s}\033[39m'


def xprint(
    *values, 
    color: str = '', 
    do_exit: bool = False, 
    exit_code: int = -1, 
    **kwargs
) -> None:
    """
    xbot 专用 print 函数。
    """
    if color:
        values = [ColorText.wrap(v, color) for v in values]
    print(*values, **kwargs)
    if do_exit:
        exit(exit_code)


printerr = functools.partial(xprint, 'error:', color='red', do_exit=True)


def render_write(template: str, outfile: str, **kwargs) -> None:
    """
    渲染并写入文件。
    
    :param template: 模板文件。
    :param outfile: 输出文件。
    """
    rendered_content = ''
    with open(template) as fp:
        tpl = jinja2.Template(fp.read())
        rendered_content = tpl.render(**kwargs)
    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    with open(outfile, 'w') as fp:
        fp.write(rendered_content)


def stop_thread(thread: Thread, exc: Exception = SystemExit):
    """通过让线程主动抛出异常的方式以结束线程
    
    :param thread: 线程实例
    :param exc: 异常类型
    :raises SystemError: 停止线程失败
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
    深度路径分割

    >>> parse_deepkey('a.b1')
    ['a', 'b1']
    >>> parse_deepkey('a.b2[0]')
    ['a', 'b2', 0]
    >>> parse_deepkey('a.b2[0].c2')
    ['a', 'b2', 0, 'c2']

    :param deepkey: 深度路径
    :param sep: 分隔符
    :return: 列表格式的深度路径
    """
    keys = []
    for k in re.split(r'%s|\[' % re.escape(sep), deepkey):
        if k.endswith(']') and k[:-1].isdigit():
            keys.append(int(k[:-1]))
        else:
            keys.append(k)
    return keys


def deepget(obj: object, deepkey: str, sep: str = '.') -> any:
    """
    深度获取对象中的值

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

    :param obj: 对象
    :param deepkey: 深度路径
    :param sep: 分隔符
    :return: 获取到的值
    """
    keys = parse_deepkey(deepkey, sep)
    return reduce(operator.getitem, keys, obj)


def deepset(obj: object, deepkey: str, value: any, sep: str = '.') -> None:
    """
    深度设置对象中的值。
    如果路径不存在则创建（路径中带索引的情况除外，如 a.b[0]）

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

    :param obj: 对象
    :param deepkey: 深度路径
    :param value: 待设置的值
    :param sep: 分隔符
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

    :param ip: IP 地址
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
    检查端口是否开放

    :param ip: IP 地址
    :param port: 端口号
    """
    try:
        conn = socket.create_connection((ip, port), 0.1)
        conn.close()
        return True
    except:
        return False