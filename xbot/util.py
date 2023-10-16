# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Utility functions.
"""

import os
import jinja2
import functools
import ctypes

from threading import Thread


class ColorText(object):
    """
    Terminal text color.
    """

    COLORS = {
        'red': '31m',
        'green': '32m',
        'yellow': '33m'
    }

    @staticmethod
    def wrap(s, color):
        """
        Color the str `s`.
        """
        code = ColorText.COLORS.get(color, None)
        if not code:
            raise ValueError(f'Not supported color: {color}')
        return f'\033[{code}{s}\033[39m'


def xprint(*values, color, do_exit=False, exit_code=-1, **kwargs):
    """
    Print function for xbot.
    """
    if color:
        values = [ColorText.wrap(v, color) for v in values]
    print(*values, **kwargs)
    if do_exit:
        exit(exit_code)


printerr = functools.partial(xprint, 'error:', color='red', do_exit=True)


def render_write(template, outfile, **kwargs):
    """
    Render the `template` and write to `outfile`.
    
    :param template: html template.
    :param outfile: output file.
    """
    rendered_content = ''
    with open(template) as fp:
        tpl = jinja2.Template(fp.read())
        rendered_content = tpl.render(**kwargs)
    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    with open(outfile, 'w') as fp:
        fp.write(rendered_content)


def stop_thread(thread, exc=SystemExit):
    """
    Stop thread by raising an exception.
    
    :param thread: Thread instance.
    :param exc: Exception to raise.
    :raises SystemError: If stop thread failed.
    """
    r = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), ctypes.py_object(exc))
    if r == 0:
        raise ValueError("Invalid thread id '%s'" % thread.ident)
    if r != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), None)
        raise SystemError("Stop thread '%s' failed" % thread.name)


def parse_deepkey(deepkey, sep='.'):
    """
    Parse deepkey to list.

    >>> parse_deepkey('a.b1')
    ['a', 'b1']
    >>> parse_deepkey('a.b2[0]')
    ['a', 'b2', 0]
    >>> parse_deepkey('a.b2[0].c2')
    ['a', 'b2', 0, 'c2']

    :param deepkey: deepkey string.
    :param sep: separator.
    :return: list of keys.
    """
    keys = []
    for k in re.split(r'%s|\[' % re.escape(sep), deepkey):
        if k.endswith(']') and k[:-1].isdigit():
            keys.append(int(k[:-1]))
        else:
            keys.append(k)
    return keys


def deepget(obj, deepkey, sep='.'):
    """
    Deep get value from object.

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

    :param obj: object.
    :param deepkey: deepkey string.
    :param sep: separator for deepkey.
    :return: value.
    """
    keys = parse_deepkey(deepkey, sep)
    return reduce(operator.getitem, keys, obj)


def deepset(obj, deepkey, value, sep='.'):
    """
    Deep set value to object.
    Create path if not exists(except for path with index, e.g. a.b[0])

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

    :param obj: Object.
    :param deepkey: deepkey string.
    :param value: value to set.
    :param sep: separator for deepkey.
    """
    keys = parse_deepkey(deepkey, sep)
    for k in keys[:-1]:
        try:
            obj = operator.getitem(obj, k)
        except KeyError:
            obj[k] = {}
            obj = obj[k]
    operator.setitem(obj, keys[-1], value)


def ip_reachable(ip):
    """
    Check if IP address is reachable.

    :param ip: IP address.
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
    Check if port is opened.

    :param ip: IP address.
    :param port: Port number.
    """
    try:
        conn = socket.create_connection((ip, port), 0.1)
        conn.close()
        return True
    except:
        return False
    