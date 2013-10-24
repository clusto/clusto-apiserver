#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import sys
from suites import coding_style
import unittest


def test_suites():
    allsuites = []
    for s in (coding_style,):
        allsuites.append(s.testcases())
    alltests = unittest.TestSuite(allsuites)
    return alltests


def main():
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suites())


if __name__ == '__main__':
    sys.exit(main())
