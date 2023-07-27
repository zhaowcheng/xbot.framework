# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
实用函数。
"""

import jinja2
import functools


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
    with open(outfile, 'w') as fp:
        fp.write(rendered_content)
