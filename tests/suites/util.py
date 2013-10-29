#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import clustoapi
import os
import socket
import threading
import time


TOP_DIR = os.path.realpath('%s/../../' % (os.path.dirname(os.path.realpath(__file__)),))
TEST_DIR = os.path.realpath('%s/../' % (os.path.dirname(os.path.realpath(__file__)),))
SRC_DIR = os.path.join(TOP_DIR, 'src')


def get_mount_apps():
    mount_apps = {}
    for app in clustoapi.apps.__all__:
        mod = 'clustoapi.apps.%s' % (app,)
        mount_apps['/%s' % (app,)] = mod

    return mount_apps


def start_testing_web_server(port):
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
