#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
# Copyright 2013, Jorge Gallegos <kad@blegh.net>

"""
The Clusto API Server will work as an alternative to the direct database
access traditional clusto commands and libraries use.

Sometimes your database has restricted access or you want to expose your clusto
information across facilities but don't want to risk opening up your database
port to the outside world or don't have the required know-how to do it in a
secure manner.

Exposing an HTTP(S) endpoint is a more common problem and as such there are
several well-understood solutions. Scalability and security are also points
you have to consider.

The Clusto API Server should thus have the following required features:

 *  Complete object manipulation: create, delete, insert, and remove objects,
    besides displaying them.
 *  Complete object attribute manipulation: add, delete, update, query, and
    displaying attributes
 *  Resource manipulation: allocate and deallocate objects from resources
 *  Querying
"""

import bottle
import clusto
from clusto import script_helper
from clusto.services import config as service
import os
import sys
import types


MODULE_INDEX = {}
root_app = bottle.Bottle()


@root_app.get('/favicon.ico')
def never_again():
    """
Send an HTTP code to clients so they stop asking for favicon
"""

    bottle.abort(410)


@root_app.get('/')
@root_app.get('/__doc__')
def build_docs():
    """
This will build documentation for the given module and all its methods.
If python-rest is available, it will attempt to parse it as a restructured
text document.
"""

#   Get the request path so we can look at the module index
    path = '/'.join(bottle.request.path.split('/')[0:-1])
    if not path:
        path = '/'
    mod = MODULE_INDEX[path]
    docs = ['\n%s\n%s\n%s\n%s' % (
        '=' * len(mod.__name__),
        mod.__name__,
        '=' * len(mod.__name__),
        mod.__doc__)]

#   Build a "TOC" with all mounted apps
    if path == '/':
        mods = []
        fullurl = bottle.request.urlparts.geturl()[0:-1]
        for mount, module in MODULE_INDEX.items():
            if mount != '/':
                mods.append('\n * `%s <%s%s/__doc__>`_\n' % (
                    module.__name__, fullurl, mount,))
        if mods:
            docs.append('\nMounted Applications\n%s\n' % ('-' * 20, ))
            docs.extend(mods)

    docs.append('\nDocument strings for this module\n%s\n' % ('-' * 32,))
    for name in dir(mod):
        method = getattr(mod, name)
        if hasattr(method, '__call__') and \
                isinstance(method, types.FunctionType):
            docs.append(
                '\n%s()\n%s\n%s' % (
                    name, '~' * (len(name) + 2), method.__doc__)
            )

    text = '\n'.join(docs)
    try:
        from docutils import core
        return core.publish_string(source=text, writer_name='html')
    except ImportError:
        bottle.response.content_type = 'text/plain'
        return text

def main():
    """
Main entry point for the clusto-apiserver console program
"""

    cfg = script_helper.load_config(os.environ.get('CLUSTOCONFIG',
                                    '/etc/clusto/clusto.conf'))
    clusto.connect(cfg)
    bind_host = service.conf('apiserver.bind', default='127.0.0.1')
    bind_port = service.conf('apiserver.port', default='9664')
    wsgi_server = service.conf('apiserver.server', default='wsgiref')
    mount_apps = service.conf('apiserver.apps')
    debug = service.conf('apiserver.debug', default=False)

#   Dynamically load all mount points from services.conf
    for mount_point, cls in mount_apps.items():
        module = __import__(cls, fromlist=[cls])
        root_app.mount(mount_point, module.bottle_app)
        root_app.route('%s/__doc__' % (mount_point,), 'GET', build_docs)
        MODULE_INDEX[mount_point] = module

    MODULE_INDEX['/'] = sys.modules[__name__]

    bottle.run(root_app, host=bind_host, port=bind_port,
               server=wsgi_server, debug=debug, reloader=debug, interval=1)


if __name__ == '__main__':
    sys.exit(main())
