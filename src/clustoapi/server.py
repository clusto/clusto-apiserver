#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

"""
Some docs
"""

import bottle
import clusto
from clusto import script_helper
from clusto.services import config as service
import os
import sys
import types


root_app = bottle.Bottle()


@root_app.get('/')
@root_app.get('/__doc__')
def build_docs(module=__name__):
    """
This will build documentation for the given module and all its methods.
If python-rest is available, it will attempt to parse it as a restructured
text document.
    """

    mod = sys.modules[module]
    docs = ['\n%s\n%s\n%s' % (
        mod.__name__, '=' * len(mod.__name__), mod.__doc__)]

    for name in dir(mod):
        method = getattr(mod, name)
        if hasattr(method, '__call__') and type(method) == types.FunctionType:
            docs.append(
                '\n%s\n%s\n%s' % (name, '-' * len(name), method.__doc__)
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

#   Dynamically load all mount points from services.conf
    for point, cls in mount_apps.items():
        module = __import__(cls, fromlist=[cls])
        root_app.mount('/%s' % (point,), module.app)

    #root_app.route('/__doc__', callback=build_docs(sys.modules[__name__]))
    bottle.run(root_app, host=bind_host, port=bind_port,
               server=wsgi_server, debug=True, reloader=True, interval=1)


if __name__ == '__main__':
    sys.exit(main())
