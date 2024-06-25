# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Entry script.
"""

import os
import sys
import shutil
import argparse

from importlib import import_module

from xbot.framework.version import __version__
from xbot.framework.testset import TestSet
from xbot.framework.runner import Runner
from xbot.framework.report import gen_report
from xbot.framework.utils import printerr, xprint
from xbot.framework.common import INIT_DIR


def create_parser() -> argparse.ArgumentParser:
    """
    Create cli parser.
    """
    parser = argparse.ArgumentParser(prog='xbot')
    parser.add_argument('command', choices=['init', 'run'])
    parser.add_argument('-d', '--directory', required=('init' in sys.argv), 
                        help='directory to init (required by `init` command)')
    parser.add_argument('-b', '--testbed', required=('run' in sys.argv), 
                        help='testbed filepath (required by `run` command)')
    parser.add_argument('-s', '--testset', required=('run' in sys.argv), 
                        help='testset filepath (required by `run` command)')
    parser.add_argument('-f', '--outfmt', choices=['verbose', 'brief'], default='brief',
                        help='output format (option for `run` command, options: verbose/brief, default: brief)')
    parser.add_argument('-v', '--version', action='version', version=f'xbot {__version__}')
    return parser


def init(directory: str) -> None:
    """
    Initialize a workdir.

    :param directory: workdir path.
    """
    if os.path.exists(directory):
        printerr('%s already exists' % directory)
    shutil.copytree(INIT_DIR, directory)
    xprint('Initialized %s' % directory)


def is_projdir(directory: str) -> bool:
    """
    Check if the `directory` is a workdir.

    :param directory: directory path.
    """
    return os.path.exists(os.path.join(directory, 'testcases'))
    

def run(testbed: str, testset: str, outfmt: str = 'brief') -> None:
    """
    Run testcases.

    :param testbed: testbed filepath.
    :param testset: testset filepath.
    :param outfmt: output format.
    """
    if not is_projdir(os.getcwd()):
        printerr("No `testcases` directory in current directory, "
                 "maybe current is not a project directory.")
    sys.path.insert(0, os.getcwd())
    tb = import_module('lib.testbed').TestBed(testbed)
    ts = TestSet(testset)
    runner = Runner(tb, ts)
    logdir = runner.run(outfmt)
    xprint('\nreport: ', end='')
    report, is_allpassed = gen_report(logdir)
    xprint(report, '\n', do_exit=True, exit_code=(not is_allpassed))


def main() -> None:
    """
    Entry function.
    """
    parser = create_parser()
    args = parser.parse_args()
    if args.command == 'init':
        init(args.directory)
    elif args.command == 'run':
        run(args.testbed, args.testset, args.outfmt)



if __name__ == '__main__':
    main()
