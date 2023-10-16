# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Xbot command line interface.
"""

import os
import sys
import shutil
import argparse

from xbot.version import __version__
from xbot.testbed import TestBed
from xbot.testset import TestSet
from xbot.runner import Runner
from xbot.report import gen_report
from xbot.util import printerr, xprint
from xbot.common import INIT_DIR


def create_parser(internal=False):
    """
    Create command line interface parser.

    :param internal: True if internal command line interface.
    """
    cmds = ['run']
    if internal:
        cmds += ['init']
    parser = argparse.ArgumentParser(prog='xbot')
    parser.add_argument('command', choices=cmds)
    if 'init' in cmds:
        parser.add_argument('-d', '--directory', required=('init' in sys.argv), help='directory to init')
    if 'run' in cmds:
        parser.add_argument('-b', '--testbed', required=('run' in sys.argv), help='testbed file')
        parser.add_argument('-s', '--testset', required=('run' in sys.argv), help='testset file')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    return parser


def init(directory):
    """
    Initialize directory.

    :param directory: directory to init.
    """
    if os.path.exists(directory):
        printerr('%s already exists.' % directory)
    shutil.copytree(INIT_DIR, directory)
    xprint('Initialized %s.' % directory)
    

def run(tbcls, testbed, testset):
    """
    Run testcases.

    :param tbcls: TestBed class.
    :param testbed: testbed file.
    :param testset: testset file.
    """
    tb = tbcls(testbed)
    ts = TestSet(testset)
    logdir = Runner(tb, ts)
    xprint('\nGenerating report...  ', end='')
    report_filepath, is_allpassed = gen_report(logdir)
    xprint(report_filepath, '\n', color='green', 
           do_exit=True, exit_code=(not is_allpassed))


def main(tbcls=TestBed, internal=False):
    """
    Main function.

    :param tbcls: TestBed class.
    :param internal: True if internal command line interface.
    """
    parser = create_parser(internal=internal)
    args = parser.parse_args()
    if args.command == 'init':
        init(args.directory)
    elif args.command == 'run':
        run(tbcls, args.testbed, args.testset)


if __name__ == '__main__':
    main(internal=True)
