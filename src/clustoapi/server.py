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
import os
import string
import sys
import types


MODULE_INDEX = {}
root_app = bottle.Bottle()


def get_url(path=False):
    """
Returns the server's normalized URL
"""

    (scheme, netloc, qpath, qs, fragment) = bottle.request.urlparts
    if path:
        return u'%s://%s%s' % (scheme, netloc, qpath)
    else:
        return u'%s://%s' % (scheme, netloc)


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
    url = get_url()
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
        for mount, module in MODULE_INDEX.items():
            if mount != '/':
                mods.append('\n * `%s <${server_url}%s/__doc__>`_\n' % (
                    module.__name__, mount,))
        if mods:
            docs.append('\nMounted Applications\n%s\n' % ('-' * 20, ))
            docs.extend(mods)

    docs.append('\nDocument strings for this module\n%s\n' % ('-' * 32,))
    toc = []
    methods = []
    for name in dir(mod):
        method = getattr(mod, name)
        if hasattr(method, '__call__') and \
                isinstance(method, types.FunctionType):
            toc.append('\n * `%s()`_' % (name,))
            methods.append(
                '\n%s()\n%s\n%s' % (
                    name, '~' * (len(name) + 2), method.__doc__)
            )

    docs.extend(toc)
    docs.extend(methods)

    tpl = string.Template('\n'.join(docs))
    text = tpl.safe_substitute(server_url=url)
    try:
        from docutils import core
        return core.publish_string(source=text, writer_name='html')
    except ImportError:
        bottle.response.content_type = 'text/plain'
        return text


def configure(config={}):
    """
Configure the root app
"""

    cfg = script_helper.load_config(os.environ.get('CLUSTOCONFIG',
                                    '/etc/clusto/clusto.conf'))
    clusto.connect(cfg)
    kwargs = {}
    kwargs['host'] = config.get(
        'bind',
        script_helper.get_conf(
            cfg, 'apiserver.bind', default='0.0.0.0'
        ),
    )
    kwargs['port'] = config.get(
        'port',
        script_helper.get_conf(
            cfg, 'apiserver.port', default='9664'
        ),
    )
    kwargs['server'] = config.get(
        'server',
        script_helper.get_conf(
            cfg, 'apiserver.server', default='wsgiref'
        ),
    )
    kwargs['debug'] = config.get(
        'debug',
        script_helper.get_conf(
            cfg, 'apiserver.debug', default=False
        )
    )
    mount_apps = {}
    if 'apps' in config:
        mount_apps = config['apps']
    else:
        apps = script_helper.get_conf(cfg, 'apiserver.apps', default='').split(',')
        for app in apps:
            if app:
                mount, aclass = app.split(':')
                mount_apps[mount] = aclass

    for mount_point, cls in mount_apps.items():
        sys.stderr.write('Mounting %s in %s\n' % (cls, mount_point,))
        module = __import__(cls, fromlist=[cls])
        root_app.mount(mount_point, module.bottle_app)
        root_app.route('%s/__doc__' % (mount_point,), 'GET', build_docs)
        MODULE_INDEX[mount_point] = module

    MODULE_INDEX['/'] = sys.modules[__name__]

    return kwargs


def main():
    """
Main entry point for the clusto-apiserver console program
"""
    kwargs = configure()
    root_app.run(**kwargs)


if __name__ == '__main__':
    sys.exit(main())
