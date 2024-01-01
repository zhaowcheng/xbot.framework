# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

import os

from setuptools import setup, find_packages


BASEDIR = os.path.abspath(os.path.dirname(__file__))


def find_version():
    verfile = os.path.join(BASEDIR, 'xbot', 'version.py')
    with open(verfile, 'r') as f:
        for line in f.readlines():
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip("'").strip('"')


def find_requires():
    reqfile = os.path.join(BASEDIR, 'requirements.txt')
    with open(reqfile, 'r') as f:
        return [r.strip() for r in f.readlines()]


setup(
    name='xbot',
    version='0.1.0',
    install_requires=find_requires(),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'xbot = xbot.main:main'
        ]
    },
    include_package_data=True,
)
