#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import clustoapi
import doctest
import os
import port_for
import socket
import sys
import shelldoctest
import string
import threading
import time
import unittest


TOP_DIR = os.path.realpath('%s/../../' % (os.path.dirname(os.path.realpath(__file__)),))
PORT = port_for.select_random()
mounts = {}
for app in clustoapi.apps.__all__:
    mod = 'clustoapi.apps.%s' % (app,)
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
for i in range(100):
    time.sleep(0.1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', PORT))
        s.close()
        break
    except socket.error:
        continue


class TemplatedShellDocTestParser(shelldoctest.ShellDocTestParser):

    def __init__(self, substitutions={}):
        self.substitutions = substitutions

    def parse(self, svalue, name='<string>'):
        tpl = string.Template(svalue)
        text = tpl.safe_substitute(**self.substitutions)
        output = shelldoctest.ShellDocTestParser.parse(self, text, name)
        return output


def test_cases():
    filenames = [os.path.join(TOP_DIR, 'src', 'clustoapi', 'server.py')]
    for walkable in ('apps',):
        for root, dirs, files in os.walk(
            os.path.join(TOP_DIR, 'src', 'clustoapi', walkable)
        ):
            for f in files:
                filename = os.path.join(root, f)
                if f.endswith('.py') and os.path.getsize(filename) > 0:
                    filenames.append(filename)
    shell_docsuite = unittest.TestSuite()
    for filename in filenames:
        suite = doctest.DocFileSuite(
            filename,
            module_relative=False,
            parser=TemplatedShellDocTestParser(
                substitutions={'server_url': 'http://127.0.0.1:%s' % (PORT,)},
            ),
            globs={
                'system_command': shelldoctest.system_command,
            },
            optionflags=doctest.ELLIPSIS,
        )
        shell_docsuite.addTest(suite)
    return suite


def main():
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_cases())


if __name__ == '__main__':
    sys.exit(main())
