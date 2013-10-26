#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

from clustoapi import server
from clustoapi import apps
import doctest
import port_for
import socket
import sys
import shelldoctest
import string
import threading
import time
import unittest


class TemplatedShellDocTestParser(shelldoctest.ShellDocTestParser):

    def __init__(self, substitutions={}):
        self.substitutions = substitutions

    def parse(self, svalue, name='<string>'):
        tpl = string.Template(svalue)
        text = tpl.safe_substitute(**self.substitutions)
        output = shelldoctest.ShellDocTestParser.parse(self, text, name)
        return output


class TestingWebServer(threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.bottle_kwargs = server.configure({'quiet': True, 'port': port, })
        self.bottle = server.root_app
        self.name = 'Bottle-%d' % (port,)
        self.port = port
        self.daemon = True

    def ping(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', self.port))
            s.close()
            return True
        except socket.error:
            return False

    def run(self):
        self.bottle.run(**self.bottle_kwargs)

    def shutdown(self):
        self.bottle.close()

class ShellDocTestSuite(unittest.TestSuite):

    def __init__(self, module):
        unittest.TestSuite.__init__(self)
        self.port = port_for.select_random()
        finder = doctest.DocTestFinder(
            parser=TemplatedShellDocTestParser(
                substitutions={'server_url': 'http://127.0.0.1:%s' % (self.port,)},
            ),
            exclude_empty=False
        )
        suite = doctest.DocTestSuite(
            module, test_finder=finder,
            globs={'system_command': shelldoctest.system_command},
            setUp=self.setUp,
            tearDown=self.tearDown,
        )
        for test in suite._tests:
            self.addTest(test)

    def setUp(self, *args):
        if not hasattr(self, 'thread'):
            self.thread = TestingWebServer(self.port)
        if not self.thread.is_alive():
            self.thread.start()
            for i in range(100):
                time.sleep(0.1)
                if self.thread.ping():
                    break

    def tearDown(self, *args):
        self.thread.shutdown()
        self.thread.join(3)



def test_cases():
    doctest_suite = ShellDocTestSuite(server)
    for app in apps.__all__:
        mod = 'clustoapi.apps.%s' % (app,)
        module = __import__(mod, fromlist=[mod])
        doctest_suite.addTests(ShellDocTestSuite(module))
    return doctest_suite


def main():
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_cases())


if __name__ == '__main__':
    sys.exit(main())
