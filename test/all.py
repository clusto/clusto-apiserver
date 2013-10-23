#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

from suites import coding_style
import sys
import unittest


def suites():
    allsuites = []
    for suite in (coding_style,):
        allsuites.append(suite.suite())
    alltests = unittest.TestSuite(allsuites)
    return alltests

def main():
    runner = unittest.TextTestRunner()
    runner.run(suites())


if __name__ == '__main__':
    sys.exit(main())
