#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import bottle
import clusto
import clustoapi
from clustoapi import apps as api_apps
import inspect
import os
import socket
import threading
import time
from wsgiref import simple_server


TOP_DIR = os.path.realpath('%s/../../' % (os.path.dirname(os.path.realpath(__file__)),))
TEST_DIR = os.path.realpath('%s/../' % (os.path.dirname(os.path.realpath(__file__)),))


class TestingWSGIServer(bottle.ServerAdapter):

    server = None

    def run(self, handler):
        class QuietHandler(simple_server.WSGIRequestHandler):
            def log_request(*args, **kw):
                pass
        self.options['handler_class'] = QuietHandler
        self.server = simple_server.make_server(
            self.host, self.port, handler, **self.options
        )
        self.server.serve_forever()

    def set_kwargs(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


class TestingServer(threading.Thread):

    def __init__(self, port):
        self.port = port
        threading.Thread.__init__(self)

    def run(self):
        conffile = config_for_testing()
        self.server = TestingWSGIServer()
        self.kwargs = clustoapi.server._configure(
            config={
                'quiet': True,
                'port': self.port,
                'host': '127.0.0.1',
                'apps': get_mount_apps(),
                'server': self.server,
            },
            configfile=conffile,
            init_data={
                'emptypool': {'driver': clusto.drivers.pool.Pool},
                'singlepool': {'driver': clusto.drivers.pool.Pool},
                'multipool': {'driver': clusto.drivers.pool.Pool},
                'testserver1': {
                    'driver': clusto.drivers.servers.BasicServer,
                    'member_of': ['singlepool', 'multipool'],
                    'attr_list': [
                        {'key': 'key1', 'subkey': 'subkey1', 'value': 'value1'}
                    ]
                },
                'testserver2': {
                    'driver': clusto.drivers.servers.BasicServer,
                    'member_of': ['multipool'],
                    'attr_list': [
                        {'key': 'key1', 'subkey': 'subkey2', 'value': 'value2'}
                    ]
                },
                'testnames': {
                    'driver': clusto.drivers.resourcemanagers.SimpleEntityNameManager,
                    'attrs': {'basename': 's'},
                },
            }
        )
        mount_apps = {}

        self.bottle = clustoapi.server.root_app

        for mount_point, cls in mount_apps.items():
            module = __import__(cls, fromlist=[cls])
            self.bottle.mount(mount_point, module.bottle_app)

        self.server.set_kwargs(**self.kwargs)
        self.startup()

    def startup(self):
        self.bottle.run(**self.kwargs)

    def shutdown(self):
        self.bottle.close()
        self.server.stop()


def config_for_testing():
    """
Write a clusto config file for testing purposes, also unlink any sqlite
databases around in preparation to run a new test suite.
    """

    conf_file = os.path.join(TEST_DIR, 'clustotest.conf')
    sqlite_file = os.path.join(TEST_DIR, 'clustotest.db')
    if os.path.isfile(sqlite_file):
        os.unlink(sqlite_file)
    f = open(conf_file, 'wb')
    f.writelines(['[clusto]\n', 'dsn = sqlite:///%s' % (sqlite_file,)])
    f.close()
    return conf_file


def get_mount_apps():
    """
Return all apps as mountable apps for the main server.
    """

    mount_apps = {}
    for app in api_apps.__all__:
        mod = 'clustoapi.apps.%s' % (app,)
        mount_apps['/%s' % (app,)] = mod

    return mount_apps


def ping(port):
    """
Ping the given port until it can establish a TCP connection.
    """

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', port))
        s.close()
        return True
    except socket.error:
        time.sleep(0.1)
        return False


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

    filenames = [os.path.join(TOP_DIR, 'clustoapi', 'server.py')]
    for walkable in ('apps',):
        for root, dirs, files in os.walk(
            os.path.join(TOP_DIR, 'clustoapi', walkable)
        ):
            for f in files:
                filename = os.path.join(root, f)
                if f.endswith('.py') and os.path.getsize(filename) > 0:
                    filenames.append(filename)

    return filenames
