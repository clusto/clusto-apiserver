#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
# Copyright 2010, Ron Gorodetzky <ron@parktree.net>
# Copyright 2010, Jeremy Grosser <jeremy@synack.me>
# Copyright 2013, Jorge Gallegos <kad@blegh.net>

"""
The ``entity`` application will hold all methods related to entity management
in clusto. That is: creation, querying, modification and overall entity
manipulation.
"""

import bottle
from bottle import request
import clusto
from clustoapi import util


bottle_app = bottle.Bottle(autojson=False)
bottle_app.config['source_module'] = __name__


@bottle_app.get('/')
@bottle_app.get('/<driver>')
def get_entities(driver=None):
    """
Returns all entities, or (optionally) all entities of the given driver

Example:

.. code:: bash

    $ ${get} ${server_url}/entity/
    [
        ...
    ]
    HTTP: 200
    Content-type: application/json

Will list all entities

Example:

.. code:: bash

    $ ${get} ${server_url}/entity/clustometa
    [
        "/clustometa/clustometa"
    ]
    HTTP: 200
    Content-type: application/json

Will list all entities that match the driver ``clustometa``

The following example should fail because there is no driver ``nondriver``:

.. code:: bash

    $ ${get} ${server_url}/entity/nondriver
    "The requested driver \"nondriver\" does not exist"
    HTTP: 409
    Content-type: application/json

"""

    result = []
    kwargs = {}
    for param in request.params.keys():
        kwargs[param] = request.params.getall(param)
    if driver:
        if driver in clusto.driverlist:
            kwargs['clusto_drivers'] = [clusto.driverlist[driver]]
        else:
            return util.dumps('The requested driver "%s" does not exist' % (driver,), 409)
    ents = clusto.get_entities(**kwargs)
    for ent in ents:
        result.append(util.unclusto(ent))

    result = []
    kwargs = {}
    for param in request.params.keys():
        kwargs[param] = request.params.getall(param)
    if driver:
        if driver in clusto.driverlist:
            kwargs['clusto_drivers'] = [clusto.driverlist[driver]]
    ents = clusto.get_entities(**kwargs)
    for ent in ents:
        result.append(util.unclusto(ent))
    return util.dumps(result)


@bottle_app.post('/<driver>')
def create(driver):
    """
Creates a new object of the given driver.

 *  Requires HTTP parameters ``name``

Example:

.. code:: bash

    $ ${post} -d 'name=createpool1' ${server_url}/entity/pool
    [
        "/pool/createpool1"
    ]
    HTTP: 201
    Content-type: application/json

Will create a new ``pool1`` object with a ``pool`` driver. If the
``pool1`` object already exists, the status code returned will be 202,
and you will see whatever warnings in the ``Warnings`` header:

.. code:: bash

    $ ${post_i} -d 'name=createpool1' ${server_url}/entity/pool
    HTTP/1.0 202 Accepted
    ...
    Warnings: Entity(s) /pool/createpool1 already exist(s)...
    [
        "/pool/createpool1"
    ]

If you try to create a server of an unknown driver, you should receive
a 409 status code back:

.. code:: bash

    $ ${post} -d 'name=createobject' ${server_url}/entity/nondriver
    "Requested driver \"nondriver\" does not exist"
    HTTP: 409
    Content-type: application/json

The following example:

.. code:: bash

    $ ${post_i} -d 'name=createpool1' -d 'name=createpool2' ${server_url}/entity/pool
    HTTP/1.0 202 Accepted
    ...
    Warnings: Entity(s) /pool/createpool1 already exist(s)...
    [
        "/pool/createpool1",
        "/pool/createpool2"
    ]

Will attempt to create new objects ``createpool1`` and ``createpool2`` with
a ``pool`` driver. As all objects are validated prior to creation, if any of
them already exists the return code will be 202 (Accepted) and you will get
an extra header ``Warnings`` with the message.

"""

    if driver not in clusto.driverlist:
        return util.dumps('Requested driver "%s" does not exist' % (driver,), 409)
    cls = clusto.driverlist[driver]
    names = request.params.getall('name')
    request.params.pop('name')

    found = []
    for name in names:
        try:
            found.append(util.unclusto(clusto.get_by_name(name)))
        except LookupError:
            pass

    result = []
    for name in names:
        result.append(util.unclusto(clusto.get_or_create(name, cls)))

    headers = {}
    if found:
        headers['Warnings'] = 'Entity(s) %s already exist(s)' % (','.join(found),)

    code = 201
    if found:
        code = 202
    return util.dumps(result, code, headers=headers)


@bottle_app.delete('/<driver>')
def delete(driver):
    """
Deletes an object if it matches the given driver

 *  Requires HTTP parameters ``name``

Examples:

.. code:: bash

    $ ${post} -d 'name=servercreated' ${server_url}/entity/basicserver
    [
        "/basicserver/servercreated"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${delete} -d 'name=servercreated' ${server_url}/entity/nondriver
    "Requested driver \"nondriver\" does not exist"
    HTTP: 409
    Content-type: application/json

.. code:: bash

    $ ${delete} -d 'name=servercreated' ${server_url}/entity/basicserver
    HTTP: 204
    Content-type:

.. code:: bash

    $ ${delete} -d 'name=servercreated' ${server_url}/entity/basicserver
    HTTP: 404
    Content-type: text/html; charset=UTF-8

Will create a new ``servercreated`` object with a ``basicserver`` driver. Then
it will proceed to delete it. If the operation succeeded, it will return a 200,
if the object doesn't exist, it will return a 404.

"""

    if driver not in clusto.driverlist:
        return util.dumps('Requested driver "%s" does not exist' % (driver,), 409)

    names = request.params.getall('name')

    notfound = []
    objs = []
    for name in names:
        try:
            objs.append(clusto.get_by_name(name))
        except LookupError:
            notfound.append(name)

    code = 204
    if notfound:
        code = 404
    else:
        for obj in objs:
            obj.entity.delete()

    return bottle.HTTPResponse('', code, headers={'content_type': None})


@bottle_app.get('/<driver>/<name>')
def show(driver, name):
    """
Returns a json representation of the given object

Example:

.. code:: bash

    $ ${post} -d 'name=showpool' ${server_url}/entity/pool
    [
        "/pool/showpool"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${get} ${server_url}/entity/pool/showpool
    {
        "attrs": [],
        "contents": [],
        "driver": "pool",
        "name": "showpool",
        "parents": []
    }
    HTTP: 200
    Content-type: application/json

Will return a JSON representation of the previously created ``showpool``.

"""

    obj, status, msg = util.get(name, driver)
    if not obj:
        return util.dumps(msg, status)

    return util.dumps(util.show(obj))


@bottle_app.put('/<driver>/<name>')
def insert(driver, name):
    """
Inserts the given device from the request parameters into the object

Example:

.. code:: bash

    $ ${post} -d 'name=insertpool' ${server_url}/entity/pool
    [
        "/pool/insertpool"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'name=insertserver' ${server_url}/entity/basicserver
    [
        "/basicserver/insertserver"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${put} -d 'device=insertserver' ${server_url}/entity/pool/insertpool
    {
        "attrs": [],
        "contents": [
            "/basicserver/insertserver"
        ],
        "driver": "pool",
        "name": "insertpool",
        "parents": []
    }
    HTTP: 200
    Content-type: application/json

Will:

#.  Create a pool entity called ``insertpool``
#.  Create a basicserver entity called ``insertserver``
#.  Insert the entity ``insertserver`` into the entity ``insertpool``

Examples:

.. code:: bash

    $ ${post} -d 'name=insertpool2' ${server_url}/entity/pool
    [
        "/pool/insertpool2"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'name=insertserver2' -d 'name=insertserver3' ${server_url}/entity/basicserver
    [
        "/basicserver/insertserver2",
        "/basicserver/insertserver3"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${put} -d 'device=insertserver2' -d 'device=insertserver3' ${server_url}/entity/pool/insertpool2
    {
        "attrs": [],
        "contents": [
            "/basicserver/insertserver2",
            "/basicserver/insertserver3"
        ],
        "driver": "pool",
        "name": "insertpool2",
        "parents": []
    }
    HTTP: 200
    Content-type: application/json

The above will:

#.  Create a pool entity called ``insertpool2``
#.  Create twp basicserver entities called ``insertserver2`` and ``insertserver3``
#.  Insert both basicserver entities into the pool entity

"""

    obj, status, msg = util.get(name, driver)
    if not obj:
        return util.dumps(msg, status)
    devices = request.params.getall('device')

    devobjs = []
    notfound = []
    for device in devices:
        try:
            devobjs.append(clusto.get_by_name(device))
        except LookupError:
            notfound.append(device)

    if notfound:
        bottle.abort(404, 'Objects %s do not exist and cannot be inserted into "%s"' % (','.join(notfound), name,))

    for devobj in devobjs:
        if devobj not in obj:
            obj.insert(devobj)

    return show(driver, name)
