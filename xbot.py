# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
入口。
"""

import inspect
import click

from click import Context, HelpFormatter
from lib.testbed import TestBed
from lib.testset import TestSet
from lib.runner import Runner
from lib.report import gen_report
from lib.util import xprint


class XbotCommand(click.Command):
    """
    命令基类
    """
    def format_epilog(self, ctx: Context, formatter: HelpFormatter) -> None:
        """
        epilog 不缩进的格式化
        """
        if self.epilog:
            epilog = inspect.cleandoc(self.epilog)
            formatter.write_paragraph()
            formatter.write_text(epilog)


@click.group()
@click.help_option('-h', '--help')
@click.version_option('0.0.0', '-v', '--version', prog_name='xbot')
def cli():
    pass


@cli.command(
    cls=XbotCommand,
    epilog="""
    \b
    Examples:
      python xbot.py runcases -b testbed/mytestbed.xml -s testset/mytestset.xml
    """
)
@click.option('-b', '--testbed', required=True, help='Testbed file path.')
@click.option('-s', '--testset', required=True, help='Testset file path.')
def runcases(testbed: str, testset: str) -> None:
    """
    Run testcases.
    """
    testbed = TestBed(testbed)
    testset = TestSet(testset)
    logdir = Runner().run(testbed, testset)
    xprint('\nGenerating report...  ', end='')
    report, allpassed = gen_report(logdir)
    rc = 0 if allpassed else 1
    xprint(report, '\n', do_exit=True, exit_code=rc)
        

if __name__ == '__main__':
    cli()
