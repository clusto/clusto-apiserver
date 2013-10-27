#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import clustoapi
import doctest
import port_for
import socket
import sys
import shelldoctest
import string
import threading
import time
import unittest


PORT = port_for.select_random()
MODULES = {}
mounts = {}
for app in clustoapi.apps.__all__:
    mod = 'clustoapi.apps.%s' % (app,)
    module = __import__(mod, fromlist=[mod])
    MODULES[app] = module
    mounts['/%s' % (app,)] = mod

bottle_kwargs = clustoapi.server.configure(
    {
        'quiet': True,
        'port': PORT,
        'debug': False,
        'apps': mounts
    }
)

bottle = clustoapi.server.root_app
THREAD = threading.Thread(target=bottle.run, kwargs=bottle_kwargs)
THREAD.daemon = True
THREAD.start()
print 'Waiting for test server to come up...'
for i in range(100):
    time.sleep(0.1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', PORT))
        s.close()
        break
    except socket.error:
        continue
print 'Is up.'


class TemplatedShellDocTestParser(shelldoctest.ShellDocTestParser):

    def __init__(self, substitutions={}):
        self.substitutions = substitutions

    def parse(self, svalue, name='<string>'):
        tpl = string.Template(svalue)
        text = tpl.safe_substitute(**self.substitutions)
        output = shelldoctest.ShellDocTestParser.parse(self, text, name)
        return output


class ShellDocTestSuite(unittest.TestSuite):

    globs = {
        'system_command': shelldoctest.system_command,
        'optionflags': doctest.ELLIPSIS,
    }

    def __init__(self, module):
        unittest.TestSuite.__init__(self)
        finder = doctest.DocTestFinder(
            parser=TemplatedShellDocTestParser(
                substitutions={'server_url': 'http://127.0.0.1:%s' % (PORT,)},
            ),
            exclude_empty=True,
        )
        tests = finder.find(module, globs=self.globs)
        tests.sort()
        for test in tests:
            tc = doctest.DocTestCase(test)
            self.addTest(tc)


def test_cases():
    doctest_suite = ShellDocTestSuite(clustoapi.server)
    for name, module in MODULES.items():
        doctest_suite.addTests(ShellDocTestSuite(module))
    return doctest_suite


def main():
    runner = unittest.TextTestRunner()
    runner.run(test_cases())


if __name__ == '__main__':
    sys.exit(main())
