#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import clustoapi
import doctest
import functools
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
    modules = ['clustoapi.server']
    modules.extend(util.get_mount_apps().values())
    for fname, function in util.get_public_methods(modules):
        doctest_complete.addTest(DocTestComplete(fname, function))

    doctest_docsuite.addTest(doctest_complete)

    # Now, for those that *do* have shell examples, test that they are actually correct
    for filename in util.get_source_filenames():
        suite = doctest.DocFileSuite(
            filename,
            module_relative=False,
            parser=TemplatedDocTestParser(
                substitutions={
                    'server_url': 'http://127.0.0.1:%s' % (PORT,),
                    'server_version': clustoapi.__version__,
                },
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
