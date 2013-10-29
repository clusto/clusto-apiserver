#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import clustoapi
import inspect
import os
import socket
import threading
import time


TOP_DIR = os.path.realpath('%s/../../' % (os.path.dirname(os.path.realpath(__file__)),))
TEST_DIR = os.path.realpath('%s/../' % (os.path.dirname(os.path.realpath(__file__)),))
SRC_DIR = os.path.join(TOP_DIR, 'src')


def get_mount_apps():
    """
Return all apps as mountable apps for the main server.
    """

    mount_apps = {}
    for app in clustoapi.apps.__all__:
        mod = 'clustoapi.apps.%s' % (app,)
        mount_apps['/%s' % (app,)] = mod

    return mount_apps


def start_testing_web_server(port):
    """
Start a testing web server in a non-blocking thread.
    """

    bottle_kwargs = clustoapi.server.configure(
        {
            'quiet': True,
            'port': port,
            'debug': False,
            'apps': get_mount_apps(),
        }
    )

    bottle = clustoapi.server.root_app

    # Start this server in a thread so it doesn't block
    thread = threading.Thread(target=bottle.run, kwargs=bottle_kwargs)
    thread.daemon = True
    thread.start()


def ping(port):
    """
Ping the given port until it can establish a TCP connection.
    """

    # Wait until the server is responding requests
    for i in range(100):
        time.sleep(0.1)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', port))
            s.close()
            break
        except socket.error:
            continue


def get_public_methods(mods):
    """
Get all "public" methods, i.e. all methods *not* named "main" that don't
start with an underscore. Returns a list of tuples mapping method names
and method objects.
    """

    results = []
    for mod in mods:
        module = __import__(mod, fromlist=[mod])
        for fname in dir(module):
            function = getattr(module, fname)
            if fname == 'main':
                continue
            if not fname.startswith('_') and inspect.isfunction(function):
                results.append((fname, function,))
    return results


def get_source_filenames():
    """
Get all python files so they can be tested.
    """

    filenames = [os.path.join(SRC_DIR, 'clustoapi', 'server.py')]
    for walkable in ('apps',):
        for root, dirs, files in os.walk(
            os.path.join(SRC_DIR, 'clustoapi', walkable)
        ):
            for f in files:
                filename = os.path.join(root, f)
                if f.endswith('.py') and os.path.getsize(filename) > 0:
                    filenames.append(filename)

    return filenames
