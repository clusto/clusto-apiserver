#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
from __future__ import absolute_import

import sys
import suites.coding_style as cs_suite
import unittest


def suites():
    allsuites = []
    for s in (cs_suite,):
        allsuites.append(s.testcases())
    alltests = unittest.TestSuite(allsuites)
    return alltests

def main():
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suites())


if __name__ == '__main__':
    sys.exit(main())
