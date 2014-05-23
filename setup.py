#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import setuptools
import sys

import clustoapi


install_requires = [
    'clusto>0.6',
    'bottle',
]

# only required when you are doing testing
test_requires = [
    'shelldoctest',
    'pep8',
    'port-for',
]

# These are not required, but give you nice colors in the UI
develop_requires = test_requires
develop_requires.extend([
    'docutils',
    'Pygments',
])

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
    version=clustoapi.__version__,
    packages=setuptools.find_packages(),
    author='Jorge Gallegos',
    author_email='kad@blegh.net',
    description='A clusto API server',
    license='BSD',
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'clusto-apiserver=clustoapi.server:main'
        ],
    },
    zip_safe=False,
    test_suite='tests.all.test_suites',
)
