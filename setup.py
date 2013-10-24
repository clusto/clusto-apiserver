#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import setuptools


setuptools.setup(
    name='clusto-apiserver',
    version='0.1.0',
    packages=setuptools.find_packages('src'),
    author='Jorge Gallegos',
    author_email='kad@blegh.net',
    description='A clusto API server',
    license='BSD',
    install_requires=[
        'distribute',
        'clusto>0.6',
        'bottle',
    ],
    entry_points={
        'console_scripts': [
            'clusto-apiserver=clustoapi.server:main'
        ],
    },
    zip_safe=False,
    package_dir={
        '': 'src'
    },
    tests_require=[
        'shelldoctest',
        'pep8',
    ],
    test_suite='test.all.suites',
)
