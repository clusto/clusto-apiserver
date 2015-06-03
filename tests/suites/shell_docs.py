#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import clustoapi
from clustoapi import server
import doctest
import functools
import port_for
import sys
import shelldoctest
import string
import unittest
import util


# Select a random port to spin up this testing server
PORT = port_for.select_random()
THREADS = {}
#THREAD.daemon = True


def setUp(dt):

    THREADS[dt] = util.TestingServer(PORT)
    THREADS[dt].start()
    count = 0
    while not util.ping(PORT) and count < 50:
        count += 1


def tearDown(dt):

    THREADS[dt].shutdown()
    count = 0
    while util.ping(PORT) and count < 50:
        count += 1


class TemplatedShellDocTestParser(shelldoctest.ShellDocTestParser):

    """
    A Regular ShellDocTestParser that passes the test through a string.Template
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
        output = shelldoctest.ShellDocTestParser.parse(self, text, name)
        # Replace double quoted json with escapes so it gets through to curl correctly.
        # \\\\\\" will turn into \\\" for python which will turn into " for curl. yay.
        for i, line in enumerate(output):
            if isinstance(line, shelldoctest.ShellExample):
                cmd = line.source.replace('"','\\\\\\\"')
                output[i].source = cmd.replace('(\\\\\\"','("').replace('\\\\\\")','")')

        return output


class ShellDocComplete(unittest.TestCase):

    def __init__(self, functionname, function):
        f = functools.partial(self.shelldoc, function)
        f.__doc__ = 'At least one ShellDoc example for %s.%s' % (function.__module__, functionname,)
        methodname = 'test_shell_example_%s_%s' % (
            function.__module__.replace('.', '_'),
            functionname.replace('.', '_'),
        )
        self.__setattr__(methodname, f)
        unittest.TestCase.__init__(self, methodname)

    def shelldoc(self, function):
        "ShellDoc completeness partial check"
        # we don't care about strings here, just that there is at least 1 example
        finder = doctest.DocTestFinder(
            parser=shelldoctest.ShellDocTestParser(),
            exclude_empty=False,
        )
        shelldocs = finder.find(function)
        for sd in shelldocs:
            self.assertGreater(
                len(sd.examples), 0,
                msg='All public functions must have at least 1 shell example'
            )


def test_cases():
    shell_docsuite = unittest.TestSuite()

    # Test for at least one example in all public methods on each mounted app
    shelldoc_complete = unittest.TestSuite()

    modules = ['clustoapi.server']
    modules.extend(util.get_mount_apps().values())
    for fname, function in util.get_public_methods(modules):
        shelldoc_complete.addTest(ShellDocComplete(fname, function))

    shell_docsuite.addTest(shelldoc_complete)

    # Now, for those that *do* have shell examples, test that they are actually correct
    substitutions = {
        'server_url': 'http://127.0.0.1:%s' % (PORT,),
        'server_version': clustoapi.__version__,
    }
    substitutions.update(server.DOC_SUBSTITUTIONS)
    for filename in util.get_source_filenames():
        suite = doctest.DocFileSuite(
            filename,
            module_relative=False,
            parser=TemplatedShellDocTestParser(
                substitutions=substitutions,
            ),
            globs={
                'system_command': shelldoctest.system_command,
            },
            optionflags=doctest.ELLIPSIS + doctest.REPORT_NDIFF + doctest.NORMALIZE_WHITESPACE,
            setUp=setUp,
            tearDown=tearDown
        )
        shell_docsuite.addTest(suite)
    return shell_docsuite


def main():
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_cases())
    return (len(result.errors) + len(result.failures)) > 0


if __name__ == '__main__':
    sys.exit(main())
