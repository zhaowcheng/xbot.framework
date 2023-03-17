# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Utility functions.
"""

import jinja2
import functools


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
    def wrap(s: str, color: str) -> str:
        """
        Color the `s`.
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
    Print function for xbot.
    """
    if color:
        values = [ColorText.wrap(v, color) for v in values]
    print(*values, **kwargs)
    if do_exit:
        exit(exit_code)


printerr = functools.partial(xprint, 'error:', color='red', do_exit=True)


def render_write(template: str, outfile: str, **kwargs) -> None:
    """Render the `template` and write to `outfile`.
    
    :param template: html template.
    :param outfile: output file.
    """
    rendered_content = ''
    with open(template) as fp:
        tpl = jinja2.Template(fp.read())
        rendered_content = tpl.render(**kwargs)
    with open(outfile, 'w') as fp:
        fp.write(rendered_content)
