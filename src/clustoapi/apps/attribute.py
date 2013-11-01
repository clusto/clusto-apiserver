#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
# Copyright 2010, Ron Gorodetzky <ron@parktree.net>
# Copyright 2010, Jeremy Grosser <jeremy@synack.me>
# Copyright 2013, Jorge Gallegos <kad@blegh.net>

import bottle
from bottle import request
from clustoapi import util


bottle_app = bottle.Bottle()
bottle_app.config['source_module'] = __name__


@bottle_app.get('/<name>')
@bottle_app.get('/<name>/<driver>')
def attrs(name, driver=None):
    """
Query attributes from this object.

Example::

    $ curl -s -w '\\nHTTP: %{http_code}' -X POST -d 'name=attrpool1' ${server_url}/entity/pool
    [
        "/pool/attrpool1"
    ]
    HTTP: 201

    $ curl -s -w '\\nHTTP: %{http_code}' ${server_url}/attribute/attrpool1
    []
    HTTP: 200

Will show all the attributes from the object ``attrpool1``::

    $ curl -s -w '\\nHTTP: %{http_code}' ${server_url}/attribute/attrpool1/pool
    []
    HTTP: 200

Will show all the attributes from the object ``attrpool1`` **if** the driver
for ``attrpool1`` is ``pool``

Example::

    curl -d "key=owner" -d "value=joe" ${server_url}/e/server/server1

Will show the attributes for ``server1`` if their key is ``owner`` *and*
the subkey is ``joe``
"""

    attrs = []
    kwargs = dict(request.params.items())
    obj, status, msg = util.object(name, driver)
    if not obj:
        return util.dumps(msg, status)

    for attr in obj.attrs(**kwargs):
        attrs.append(util.unclusto(attr))
    return util.dumps(attrs)


@bottle_app.post('/<name>')
@bottle_app.post('/<name>/<driver>')
def add_attr(name, driver=None):
    """
Add an attribute to this object.

 *  Requires HTTP parameters ``name``, ``key``, and ``value``
 *  Optional parameters are ``subkey`` and ``number``

Example::

    $ curl -s -w '\\nHTTP: %{http_code}' -X POST -d 'name=addattrserver' ${server_url}/entity/basicserver
    [
        "/basicserver/addattrserver"
    ]
    HTTP: 201

    $ curl -s -w '\\nHTTP: %{http_code}' -X POST -d 'key=group' -d 'value=web' ${server_url}/attribute/addattrserver
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "web"
        }
    ]
    HTTP: 200

Will:

#.  Create an entity called ``addattrserver``
#.  Add the attribute with ``key=group`` and ``value=web`` to it

Example::

    $ curl -s -w '\\nHTTP: %{http_code}' -X POST -d 'key=group' -d 'subkey=owner' -d 'value=web' ${server_url}/attribute/addattrserver
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "web"
        },
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": "owner",
            "value": "web"
        }
    ]
    HTTP: 200

Will add the attribute with key ``group`` *and* subkey ``owner`` *and*
value ``joe`` to the previously created entity ``addattrserver``

"""

    kwargs = dict(request.params.items())
    obj, status, msg = util.object(name, driver)
    if not obj:
        return util.dumps(msg, status)

    for k in ('key', 'value'):
        if k not in kwargs.keys():
            bottle.abort(412, 'Provide at least "key" and "value"')

    if 'number' in kwargs:
        kwargs['number'] = int(kwargs['number'])

    obj.add_attr(**kwargs)

    return util.dumps([util.unclusto(_) for _ in obj.attrs()])


@bottle_app.put('/<name>')
@bottle_app.put('/<name>/<driver>')
def set_attr(name, driver=None):
    """
Sets an attribute from this object. If the attribute doesn't exist
it will be added, if the attribute already exists then it will be
updated.

 *  Requires HTTP parameters ``key`` and ``value``
 *  Optional parameters are ``subkey`` and ``number``

Example::

    $ curl -s -w '\\nHTTP: %{http_code}' -X POST -d 'name=setattrserver' ${server_url}/entity/basicserver
    [
        "/basicserver/setattrserver"
    ]
    HTTP: 201

    $ curl -s -w '\\nHTTP: %{http_code}' -X POST -d 'key=group' -d 'value=web' ${server_url}/attribute/setattrserver
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "web"
        }
    ]
    HTTP: 200

    $ curl -s -w '\\nHTTP: %{http_code}' -X PUT -d 'key=group' -d 'value=db' ${server_url}/attribute/setattrserver
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "db"
        }
    ]
    HTTP: 200

Will:

#.  Create the entity ``setattrserver``
#.  Add the attribute with ``key=group`` and ``value=web``
#.  Update the attribute to ``value=db``

Example::

    $ curl -s -w '\\nHTTP: %{http_code}' -X POST -d 'name=setattrserver2' ${server_url}/entity/basicserver
    [
        "/basicserver/setattrserver2"
    ]
    HTTP: 201

    $ curl -s -w '\\nHTTP: %{http_code}' -X PUT -d 'key=group' -d 'subkey=owner' -d 'value=joe' ${server_url}/attribute/setattrserver2
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": "owner",
            "value": "joe"
        }
    ]
    HTTP: 200

    $ curl -s -w '\\nHTTP: %{http_code}' -X PUT -d 'key=group' -d 'subkey=owner' -d 'value=bob' ${server_url}/attribute/setattrserver2
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": "owner",
            "value": "bob"
        }
    ]
    HTTP: 200

Will:

#.  Create a new object ``setattrserver2`` of type ``basicserver``
#.  Set the attribute with key ``group`` *and* subkey ``owner`` with value
    ``joe`` to the object ``setattrserver1``. Since this is the only attribute
    so far, this operation works just like ``add_attr()``
#.  Update the attribute we set above, now the ``value`` will read ``bob``
"""

    kwargs = dict(request.params.items())
    obj, status, msg = util.object(name, driver)
    if not obj:
        return util.dumps(msg, status)
    for k in ('key', 'value'):
        if k not in kwargs.keys():
            bottle.abort(412, 'Provide at least "key" and "value"')
    if 'number' in kwargs:
        kwargs['number'] = int(kwargs['number'])
    obj.set_attr(**kwargs)
    return util.dumps([util.unclusto(_) for _ in obj.attrs()])


@bottle_app.delete('/<name>')
@bottle_app.delete('/<name>/<driver>')
def del_attrs(name, driver=None):
    """
Deletes an attribute from this object

 *  Requires HTTP parameters ``key``
 *  Optional parameters are ``subkey``, ``value``, and ``number``

Examples::

    $ curl -s -w '\\nHTTP: %{http_code}' -X POST -d 'name=deleteserver1' ${server_url}/entity/basicserver
    [
        "/basicserver/deleteserver1"
    ]
    HTTP: 201

    $ curl -s -w '\\nHTTP: %{http_code}' -X PUT -d 'key=group' -d 'subkey=owner' -d 'value=joe' ${server_url}/attribute/deleteserver1
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": "owner",
            "value": "joe"
        }
    ]
    HTTP: 200

    $ curl -s -w '\\nHTTP: %{http_code}' -X DELETE -d 'key=group' -d 'subkey=owner' ${server_url}/attribute/deleteserver1
    []
    HTTP: 200

Will create a ``basicserver`` object called ``deleteserver1``, then it will
add an attribute (the only attribute so far), then it will delete it.

Example::

    curl -X POST -d "key=group" -d "subkey=owner" -d "value=joe" ${server_url}/e/server/server1

Will delete the attribute with key ``group`` *and* subkey ``owner`` *and*
value ``web`` from the object ``server1``.

Example::

    curl -X POST -d "key=group" ${server_url}/e/server/server1

Will delete *all the attributes* with key ``group`` from the object
``server1``, regardless of subkeys or values.
"""

    kwargs = dict(request.params.items())
    obj, status, msg = util.object(name, driver)
    if not obj:
        return util.dumps(msg, status)
    if 'key' not in kwargs.keys():
        bottle.abort(412, 'Provide at least "key" and "value"')
    if 'number' in kwargs:
        kwargs['number'] = int(kwargs['number'])
    obj.del_attrs(**kwargs)
    return util.dumps([util.unclusto(_) for _ in obj.attrs()])
