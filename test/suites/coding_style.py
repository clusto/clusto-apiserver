#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import functools
import os
import pep8
import sys
import unittest

TOP_DIR = os.path.realpath('%s/../../' % (os.path.dirname(os.path.realpath(__file__)),))


class PEP8Test(unittest.TestCase):

    def __init__(self, methodname, filename):
        f = functools.partial(self.pep8, filename)
        f.__doc__ = 'PEP8 for %s' % (filename,)
        self.__setattr__(methodname, f)
        unittest.TestCase.__init__(self, methodname)
        self.filename = filename

    def pep8(self, filename):
        "PEP8 partial check"
        pep8style = pep8.StyleGuide(config_file=os.path.join(TOP_DIR, 'setup.cfg'))
        report = pep8style.check_files([filename])
        messages = []
        if report.total_errors != 0:
            report._deferred_print.sort()
            for line_number, offset, code, text, doc in report._deferred_print:
                messages.append('Row %d Col %d: %s' % (line_number, offset + 1, text,))
        self.assertEqual(
            report.total_errors, 0, ','.join(messages))


def testcases():
    filenames = {}
    for root, dirs, files in os.walk(TOP_DIR):
        for f in files:
            filename = os.path.join(root, f)
            if f.endswith('.py') and os.path.getsize(filename) > 0:
                filekey = os.path.join(os.path.basename(root), f)
                filekey = filekey.replace('/', '_').replace('.', '_')
                filenames['test_%s' % (filekey,)] = filename
    pep8_suite = unittest.TestSuite()
    for k, v in filenames.items():
        pep8_suite.addTest(PEP8Test(k, v))
    return pep8_suite


def main():
    alltests = unittest.TestSuite([testcases()])
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(alltests)


if __name__ == '__main__':
    sys.exit(main())
