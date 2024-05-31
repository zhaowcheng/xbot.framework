# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

import os

from setuptools import setup, find_packages


BASEDIR = os.path.abspath(os.path.dirname(__file__))


def find_version():
    verfile = os.path.join(BASEDIR, 'xbot', 'version.py')
    with open(verfile, 'r', encoding='utf8') as f:
        for line in f.readlines():
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip("'").strip('"')


def find_requires():
    reqfile = os.path.join(BASEDIR, 'requirements.txt')
    with open(reqfile, 'r', encoding='utf8') as f:
        return [r.strip() for r in f.readlines()]
    

def find_long_description():
    with open('README.rst', encoding='utf8') as f:
        desc = f.read()
        desc = desc.replace('github.com/zhaowcheng/xbot/blob/master',
                            f'github.com/zhaowcheng/xbot/blob/v{find_version()}')
        return desc


setup(
    name='xbot.framework',
    version=find_version(),
    description='A lightweight, easy-to-use, and extensible automation testing framework.',
    long_description=find_long_description(),
    long_description_content_type='text/x-rst',
    author='zhaowcheng',
    author_email='zhaowcheng@163.com',
    install_requires=find_requires(),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'xbot = xbot.main:main'
        ]
    },
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12"
    ],
    url='https://github.com/zhaowcheng/xbot',
    python_requires='>=3.6',
    project_urls={
        'Homepage': 'https://github.com/zhaowcheng/xbot',
        'Issues': 'https://github.com/zhaowcheng/xbot/issues'
    }
)
