#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import doctest
import functools
import inspect
import os
import port_for
import sys
import string
import unittest
import util


# Select a random port to spin up this testing server
PORT = port_for.select_random()


def setUpModule():

    util.start_testing_web_server(PORT)
    util.ping(PORT)


class TemplatedDocTestParser(doctest.DocTestParser):

    """
    A Regular DocTestParser that passes the test through a string.Template
    object before passing it to the parser. This because I am using a variable
    in the docstrings around here so they look "correct" no matter where they
    are or how they are being served.
    """

    def __init__(self, substitutions={}):
        """
        This constructor can optionally receive a dictionary with substitution
        strings to parse via string.Template down below.
        """
        self.substitutions = substitutions

    def parse(self, svalue, name='<string>'):
        """
        Get the example, pass it through the string.Template object and then
        parse it as usual.
        """
        tpl = string.Template(svalue)
        text = tpl.safe_substitute(**self.substitutions)
        output = doctest.DocTestParser.parse(self, text, name)
        return output


class DocTestComplete(unittest.TestCase):

    def __init__(self, functionname, function):
        f = functools.partial(self.doctest, function)
        f.__doc__ = 'At least one DocTest example for %s (in %s)' % (function, functionname,)
        methodname = 'test_doctest_example_%s' % (functionname.replace('.', '_'),)
        self.__setattr__(methodname, f)
        unittest.TestCase.__init__(self, methodname)

    def doctest(self, function):
        "DocTest completeness partial check"
        # we don't care about strings here, just that there is at least 1 example
        finder = doctest.DocTestFinder()
        testdocs = finder.find(function)
        for td in testdocs:
            self.assertGreater(
                len(td.examples), 0,
                msg='All public functions must have at least 1 doctest example'
            )


def test_cases():
    doctest_docsuite = unittest.TestSuite()

    # Test for at least one example in all public methods on each mounted app
    doctest_complete = unittest.TestSuite()
    for mount_point, cls in util.get_mount_apps().items():
        module = __import__(cls, fromlist=[cls])
        for fname in dir(module):
            function = getattr(module, fname)
            if not fname.startswith('_') and inspect.isfunction(function):
                doctest_complete.addTest(DocTestComplete(cls, function))
            else:
                pass

    doctest_docsuite.addTest(doctest_complete)

    # Now, for those that *do* have shell examples, test that they are actually correct
    filenames = [os.path.join(util.SRC_DIR, 'clustoapi', 'server.py')]
    for walkable in ('apps',):
        for root, dirs, files in os.walk(
            os.path.join(util.SRC_DIR, 'clustoapi', walkable)
        ):
            for f in files:
                filename = os.path.join(root, f)
                if f.endswith('.py') and os.path.getsize(filename) > 0:
                    filenames.append(filename)
    for filename in filenames:
        suite = doctest.DocFileSuite(
            filename,
            module_relative=False,
            parser=TemplatedDocTestParser(
                substitutions={'server_url': 'http://127.0.0.1:%s' % (PORT,)},
            ),
            optionflags=doctest.ELLIPSIS,
        )
        doctest_docsuite.addTest(suite)
    return doctest_docsuite


def main():
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_cases())


if __name__ == '__main__':
    sys.exit(main())
