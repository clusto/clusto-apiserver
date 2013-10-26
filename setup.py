#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import setuptools
import sys


install_requires = [
    'distribute',
    'clusto>0.6',
    'bottle',
]

test_requires = [
    'shelldoctest',
    'pep8',
    'port-for',
]

develop_requires = test_requires

args = sys.argv[1:]
# if we are installing just punt all extra reqs and do install_requires only
if 'install' not in args:
    for arg in args:
        if arg == 'develop':
            install_requires.extend(develop_requires)
            continue
        if arg == 'test':
            install_requires.extend(test_requires)
            continue


setuptools.setup(
    name='clusto-apiserver',
    version='0.1.0',
    packages=setuptools.find_packages('src'),
    author='Jorge Gallegos',
    author_email='kad@blegh.net',
    description='A clusto API server',
    license='BSD',
    setup_requires=[
        'distribute',
    ],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'clusto-apiserver=clustoapi.server:main'
        ],
    },
    zip_safe=False,
    package_dir={
        '': 'src'
    },
    test_suite='test.all.test_suites',
)
