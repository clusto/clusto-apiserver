#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
# Copyright 2013, Jorge Gallegos <kad@blegh.net>

"""
Overview
--------

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


Custom Headers
--------------
The Clusto API Server comes with the ability to pass certain headers to
multiple operations.

:Clusto-Mode: Determines if an object is ``compact`` or ``expanded``.
  Compaction of objects helps speed up response time for multiple object
  lookups. ``expanded`` is the default mode if the function returns only one
  object, and is ``compact`` by default for all listing functions.

:Clusto-Per-Page: Number of entities to return when pagination is requested.
  Defaults to ``50``.

:Clusto-Page: Requests the current page in a list of entities, delimited by
  ``Clusto-Per-Page``.

:Clusto-Pages: Response only. This header returns the total number of pages
  to the requester.


API Docs
--------

"""

import bottle
import clusto
from clusto import script_helper
import clustoapi
import functools
import importlib
import inspect
import os
import string
import sys
import util


DOC_SUBSTITUTIONS = {
    'get': "curl -X GET -G -s -w '\\nHTTP: %{http_code}\\nContent-type: %{content_type}'",
    'get_i': "curl -X GET -G -si",
    'post': "curl -X POST -s -w '\\nHTTP: %{http_code}\\nContent-type: %{content_type}'",
    'post_i': "curl -X POST -si",
    'put': "curl -X PUT -s -w '\\nHTTP: %{http_code}\\nContent-type: %{content_type}'",
    'put_i': "curl -X PUT -si",
    'delete': "curl -X DELETE -s -w '\\nHTTP: %{http_code}\\nContent-type: %{content_type}'",
    'delete_i': "curl -X DELETE -si",
    'head': "curl -s -I",
}

root_app = bottle.Bottle(autojson=False)


def _get_url(path=False):
    """
Returns the server's normalized URL
"""

    (scheme, netloc, qpath, qs, fragment) = bottle.request.urlparts
    if path:
        return u'%s://%s%s' % (scheme, netloc, qpath)
    else:
        return u'%s://%s' % (scheme, netloc)


@root_app.get('/favicon.ico')
def favicon():
    """
Send an HTTP code to clients so they stop asking for favicon. Example:

.. code:: bash

    $ ${get} -o /dev/null ${server_url}/favicon.ico
    HTTP: 410
    Content-type: text/html; charset=UTF-8

"""

    return bottle.HTTPResponse('', status=410)


@root_app.route('/', method='HEAD')
@root_app.get('/__version__')
def version():
    """
This shows the current version running, example

.. code:: bash

    $ ${get} ${server_url}/__version__
    "${server_version}"
    HTTP: 200
    Content-type: application/json

If you make a HEAD request to the / endpoint, the response is also the version
string, as that's less heavy to build than the regular / page:

.. code:: bash

    $ ${head} ${server_url}/
    HTTP/1.0 200 OK
    ...

    """

    return clustoapi.util.dumps(clustoapi.__version__)


def _get_mounts_and_modules():
    mods = {}
    for route in root_app.routes:
        mp = route.config.get('mountpoint')
        if mp:
            target = mp.get('target')
            if target and target.config.get('source_module'):
                mods[mp['prefix']] = target.config['source_module']
    return mods


@root_app.get('/__meta__')
def meta():
    """
This call just returns a mapping of all currently installed applications.

.. code:: bash

    $ ${get} ${server_url}/__meta__
    ...
    HTTP: 200
    Content-type: application/json

"""
    return clustoapi.util.dumps(_get_mounts_and_modules())


@root_app.get('/')
@root_app.get('/__doc__')
def build_docs(path='/', module=__name__):
    """
This will build documentation for the given module and all its methods.
If python-rest is available, it will attempt to parse it as a restructured
text document. You can get to the docs by going to the __doc__ endpoint on
each mounted application, the main __doc__ endpoint, or on the main endpoint:

.. code:: bash

    $ ${get} ${server_url}/__doc__
    <?xml version="1.0" encoding="utf-8" ?>
    ...
    HTTP: 200
    Content-type: text/html; charset=UTF-8

If you pass the ``Accept`` headers and specify ``text/plain``, you should get
the plain text version back

.. code:: bash

    $ ${get} -H 'Accept: text/plain' ${server_url}/__doc__
    ...
    HTTP: 200
    Content-type: text/plain

    $ diff -q <( curl -s -H 'Accept: text/plain' ${server_url}/__doc__ ) <( curl -s -H 'Accept: text/plain' ${server_url}/ ) && echo 'equal' || echo 'diff'
    equal

"""

#   Get the request path so we can look at the module index
    mod = sys.modules[module]
    docs = ['\n%s\n%s\n%s\n%s' % (
        '=' * len(mod.__name__),
        mod.__name__,
        '=' * len(mod.__name__),
        mod.__doc__ or '')]

    if path == '/':
        mods = _get_mounts_and_modules()
        if mods:
            docs.append('\nMounted Applications\n%s\n' % ('-' * 20, ))
            for k, v in mods.items():
                docs.append(
                    '\n * `%s <${server_url}/__doc__%s>`_\n' % (v, k,)
                )

    docs.append('\nModule methods\n%s\n' % ('-' * 32,))
    toc = []
    methods = []
    for name in dir(mod):
        method = getattr(mod, name)
        if name != 'main' and not name.startswith('_') and inspect.isfunction(method):
            toc.append('\n * `%s()`_' % (name,))
            methods.append(
                '\n%s()\n%s\n%s' % (
                    name, '~' * (len(name) + 2), method.__doc__)
            )

    docs.extend(toc)
    docs.extend(methods)

    tpl = string.Template('\n'.join(docs))
    text = tpl.safe_substitute(
        server_url=_get_url(),
        server_version=clustoapi.__version__,
        **DOC_SUBSTITUTIONS
    )
    accept = bottle.request.headers.get('accept', 'text/plain')
    if accept != 'text/plain':
        try:
            from docutils import core
            return core.publish_string(source=text, writer_name='html')
        except ImportError:
            bottle.response.content_type = 'text/plain'
            return text
    else:
        bottle.response.content_type = 'text/plain'
        return text


@root_app.get('/from-pools')
def get_from_pools():
    """
One of the main ``clusto`` operations. Parameters:

* Required: at least one ``pool`` parameter
* Optional: one or more ``driver`` parameter to filter out results
* Optional: one or more ``type`` parameter to filter out results
* Optional: a boolean ``children`` parameter to search for children
  recursively (True by default)

Examples:

.. code:: bash

    $ ${get} ${server_url}/from-pools
    "Provide at least one pool to get data from"
    HTTP: 412
    Content-type: application/json

    $ ${get} -H 'Clusto-Page: notanint' -d 'pool=emptypool' ${server_url}/from-pools
    "invalid literal for int() with base 10: 'notanint'"
    HTTP: 400
    Content-type: application/json

    $ ${get} -d 'pool=emptypool' ${server_url}/from-pools
    []
    HTTP: 200
    Content-type: application/json

    $ ${get} -d 'pool=singlepool' -d 'pool=multipool' ${server_url}/from-pools
    [
        "/basicserver/testserver1"
    ]
    HTTP: 200
    Content-type: application/json

    $ ${get} -H 'Clusto-Mode: expanded' -d 'pool=multipool' ${server_url}/from-pools
    [
        {
            "attrs": [],
            "contents": [],
            "driver": "basicserver",
            "name": "testserver1",
            "parents": [
                "/pool/singlepool",
                "/pool/multipool"
            ]
        },
        {
            "attrs": [],
            "contents": [],
            "driver": "basicserver",
            "name": "testserver2",
            "parents": [
                "/pool/multipool"
            ]
        }
    ]
    HTTP: 200
    Content-type: application/json

    $ ${get} -H 'Clusto-Page: 1'  -H 'Clusto-Per-Page: 1' -d 'pool=multipool' ${server_url}/from-pools
    [
        "/basicserver/testserver1"
    ]
    HTTP: 200
    Content-type: application/json

    $ ${get} -H 'Clusto-Page: 1'  -H 'Clusto-Per-Page: 100' -d 'pool=multipool' ${server_url}/from-pools
    [
        "/basicserver/testserver1",
        "/basicserver/testserver2"
    ]
    HTTP: 200
    Content-type: application/json

    $ ${get} -H 'Clusto-Page: 100'  -H 'Clusto-Per-Page: 100' -d 'pool=multipool' ${server_url}/from-pools
    []
    HTTP: 200
    Content-type: application/json

"""

    pools = bottle.request.params.getall('pool')
    if not pools:
        return util.dumps('Provide at least one pool to get data from', 412)
    types = bottle.request.params.getall('type')
    drivers = bottle.request.params.getall('driver')
    children = bottle.request.params.get('children', default=True, type=bool)
    mode = bottle.request.headers.get('Clusto-Mode', default='compact')

    try:
        # Assignments are moved into the try block because of the int casting.
        current = int(bottle.request.headers.get('Clusto-Page', default='0'))
        per = int(bottle.request.headers.get('Clusto-Per-Page', default='50'))

        ents = clusto.get_from_pools(
            pools, clusto_types=types, clusto_drivers=drivers, search_children=children
        )
        results = []
        headers = {}
        if current:
            ents, total = util.page(list(ents), current=current, per=per)
            headers = {
                'Clusto-Pages': total,
                'Clusto-Per-Page': per,
                'Clusto-Page': current
            }
        for ent in ents:
            results.append(util.show(ent, mode))
        return util.dumps(results, headers=headers)
    except ValueError as ve:
        return util.dumps('%s' % (ve,), 400)
    except TypeError as te:
        return util.dumps('%s' % (te,), 409)
    except LookupError as le:
        return util.dumps('%s' % (le,), 404)
    except Exception as e:
        return util.dumps('%s' % (e,), 500)


@root_app.get('/by-name/<name>')
def get_by_name(name):
    """
One of the main ``clusto`` operations. Parameters:

* Required path parameter: ``name`` - The name you're looking for
* Optional: ``driver`` - If provided, a driver check will be added to
  ensure the resulting object is the type you're expecting

.. note:: This function returns expanded objects by default in order
  to reduce the amount of required custom headers. Therefore, the header
  is not required to receive expanded objects.

Examples:

.. code:: bash

    $ ${get} ${server_url}/by-name/nonserver
    "Object \"nonserver\" not found (nonserver does not exist.)"
    HTTP: 404
    Content-type: application/json

    $ ${get} -H 'Clusto-Mode: compact' ${server_url}/by-name/testserver1
    "/basicserver/testserver1"
    HTTP: 200
    Content-type: application/json

    $ ${get} ${server_url}/by-name/testserver1
    {
        "attrs": [],
        "contents": [],
        "driver": "basicserver",
        "name": "testserver1",
        "parents": [
            "/pool/singlepool",
            "/pool/multipool"
        ]
    }
    HTTP: 200
    Content-type: application/json

    $ ${get} -d 'driver=pool' ${server_url}/by-name/testserver1
    "The driver for object \"testserver1\" is not \"pool\""
    HTTP: 409
    Content-type: application/json

    $ ${get} -d 'driver=nondriver' ${server_url}/by-name/testserver1
    "The driver \"nondriver\" is not a valid driver"
    HTTP: 412
    Content-type: application/json

"""

    driver = bottle.request.params.get('driver', default=None)
    mode = bottle.request.headers.get('Clusto-Mode', default='expanded')
    obj, status, msg = util.get(name, driver)
    if not obj:
        return util.dumps(msg, status)
    try:
        return util.dumps(util.show(obj, mode))
    except TypeError as te:
        return util.dumps('%s' % (te,), 409)


@root_app.get('/by-names')
def get_by_names():
    """
One of the main ``clusto`` operations. Parameters:

* Required parameter: At least one ``name`` parameter

Returns ``HTTP: 404`` when all entites requested do not exist and
``HTTP: 206`` when a percent of entities requested do not exist.

Examples:

.. code:: bash

    $ ${get} ${server_url}/by-names
    "Provide at least one name to get data from"
    HTTP: 412
    Content-type: application/json

    $ ${get} -d 'name=nonserver' ${server_url}/by-names
    [
        null
    ]
    HTTP: 404
    Content-type: application/json

    $ ${get} -d 'name=testserver1' -d 'name=nonserver' ${server_url}/by-names
    [
        "/basicserver/testserver1",
        null
    ]
    HTTP: 206
    Content-type: application/json

    $ ${get} -H 'Clusto-Mode: expanded' -d 'name=testserver1' -d 'name=testserver2' ${server_url}/by-names
    [
        {
            "attrs": [],
            "contents": [],
            "driver": "basicserver",
            "name": "testserver1",
            "parents": [
                "/pool/singlepool",
                "/pool/multipool"
            ]
        },
        {
            "attrs": [],
            "contents": [],
            "driver": "basicserver",
            "name": "testserver2",
            "parents": [
            "/pool/multipool"
            ]
        }
    ]
    HTTP: 200
    Content-type: application/json

    $ ${get} -d 'name=nonserver1' -d 'name=nonserver2' ${server_url}/by-names
    [
        null,
        null
    ]
    HTTP: 404
    Content-type: application/json

"""

    objs = []
    names = bottle.request.params.getall('name')
    if not names:
        return util.dumps('Provide at least one name to get data from', 412)

    mode = bottle.request.headers.get('Clusto-Mode', default='compact')
    for name in names:
        obj, status, msg = util.get(name)
        try:
            objs.append(util.show(obj, mode) if obj else None)
        except TypeError as te:
            return util.dumps('%s' % (te,), 409)

    return util.dumps(objs, 200 if all(objs) else 206 if any(objs) else 404)


def _configure(config={}, configfile=None, init_data={}):
    """
Configure the root app
"""

    if configfile:
        cfg = configfile
    else:
        cfg = os.environ.get(
            'CLUSTOCONFIG',
            '/etc/clusto/clusto.conf'
        )
    cfg = script_helper.load_config(cfg)
    clusto.connect(cfg)
#   This is an idempotent operation
    clusto.init_clusto()
#   If init_data is provided, populate it in the clusto database
    if init_data:
        for name, data in init_data.items():
            ent = clusto.get_or_create(
                name,
                data['driver'],
                **data.get('attrs', {})
            )
            for pool in data.get('member_of', []):
                clusto.get_by_name(pool).insert(ent)

    kwargs = {}
    kwargs['host'] = config.get(
        'host',
        script_helper.get_conf(
            cfg, 'apiserver.host', default='127.0.0.1'
        ),
    )
    kwargs['port'] = config.get(
        'port',
        script_helper.get_conf(
            cfg, 'apiserver.port', default=9664, datatype=int
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
            cfg, 'apiserver.debug', default=False, datatype=bool
        )
    )
    kwargs['quiet'] = config.get(
        'quiet',
        script_helper.get_conf(
            cfg, 'apiserver.quiet', default=False, datatype=bool
        )
    )
    kwargs['reloader'] = config.get(
        'reloader',
        script_helper.get_conf(
            cfg, 'apiserver.reloader', default=False, datatype=bool
        )
    )
    mount_apps = config.get(
        'apps',
        script_helper.get_conf(
            cfg, 'apiserver.apps', default={}, datatype=dict
        )
    )

    root_app.route('/__doc__', 'GET', functools.partial(build_docs, '/', __name__))
    for mount_point, cls in mount_apps.items():
        module = importlib.import_module(cls)
        path = '/__doc__%s' % (mount_point,)
        root_app.route(path, 'GET', functools.partial(build_docs, path, cls))
        root_app.mount(mount_point, module.app)

    return kwargs


def main():
    """
Main entry point for the clusto-apiserver console program
"""
    kwargs = _configure()
    root_app.run(**kwargs)


if __name__ == '__main__':
    sys.exit(main())
