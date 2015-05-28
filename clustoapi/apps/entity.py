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


app = bottle.Bottle(autojson=False)
app.config['source_module'] = __name__


@app.get('/')
@app.get('/<driver>')
@app.get('/<driver>/')
def list(driver=None):
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
    HTTP: 412
    Content-type: application/json

"""

    result = []
    kwargs = {}
    mode = bottle.request.headers.get('Clusto-Mode', default='compact')
    headers = {}
    try:
        # Assignments are moved into the try block because of the int casting.
        current = int(bottle.request.headers.get('Clusto-Page', default='0'))
        per = int(bottle.request.headers.get('Clusto-Per-Page', default='50'))
    except TypeError as ve:
        return util.dumps('%s' % (ve,), 400)

    for param in request.params.keys():
        kwargs[param] = request.params.getall(param)
    if driver:
        if driver in clusto.driverlist:
            kwargs['clusto_drivers'] = [clusto.driverlist[driver]]
        else:
            return util.dumps('The requested driver "%s" does not exist' % (driver,), 412)
    ents = clusto.get_entities(**kwargs)
    if current:
        ents, total = util.page(ents, current=current, per=per)
        headers['Clusto-Pages'] = total
        headers['Clusto-Per-Page'] = per
        headers['Clusto-Page'] = current

    for ent in ents:
        result.append(util.show(ent, mode))
    return util.dumps(result, headers=headers)


@app.post('/<driver>')
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
a 412 status code back:

.. code:: bash

    $ ${post} -d 'name=createobject' ${server_url}/entity/nondriver
    "Requested driver \"nondriver\" does not exist"
    HTTP: 412
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
        return util.dumps('Requested driver "%s" does not exist' % (driver,), 412)
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


@app.delete('/<driver>/<name>')
def delete(driver, name):
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

    $ ${delete} ${server_url}/entity/nondriver/servercreated
    "Requested driver \"nondriver\" does not exist"
    HTTP: 412
    Content-type: application/json

.. code:: bash

    $ ${delete} ${server_url}/entity/basicserver/servercreated
    HTTP: 204
    Content-type:

.. code:: bash

    $ ${delete} ${server_url}/entity/basicserver/servercreated
    HTTP: 404
    Content-type: None

Will create a new ``servercreated`` object with a ``basicserver`` driver. Then
it will proceed to delete it. If the operation succeeded, it will return a 200,
if the object doesn't exist, it will return a 404.

"""

    if driver not in clusto.driverlist:
        return util.dumps('Requested driver "%s" does not exist' % (driver,), 412)

    notfound = None

    try:
        obj = clusto.get_by_name(name)
    except LookupError:
        notfound = name

    code = 204
    if notfound:
        code = 404
    else:
        obj.entity.delete()

    return bottle.HTTPResponse('', code, headers={'Content-type': None})


@app.get('/<driver>/<name>')
@app.get('/<driver>/<name>/')
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

.. code:: bash

    $ ${get} ${server_url}/entity/basicserver/showpool
    "The driver for object \"showpool\" is not \"basicserver\""
    HTTP: 409
    Content-type: application/json

Will yield a 409 (Conflict) because the object ``showpool`` is not a
``basicserver`` object.
"""

    obj, status, msg = util.get(name, driver)
    if not obj:
        return util.dumps(msg, status)

    return util.dumps(util.show(obj))


@app.post('/<driver>/<name>')
def action(driver, name):
    """
Inserts/removes the given device from the request parameters into/from the object

Example:

.. code:: bash

    $ ${post} -d 'name=pool1' ${server_url}/entity/pool
    [
        "/pool/pool1"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'name=server1' ${server_url}/entity/basicserver
    [
        "/basicserver/server1"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'device=server1' -d 'action=insert' ${server_url}/entity/pool/pool1
    {
        "attrs": [],
        "contents": [
            "/basicserver/server1"
        ],
        "driver": "pool",
        "name": "pool1",
        "parents": []
    }
    HTTP: 200
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'device=server1' -d 'action=remove' ${server_url}/entity/pool/pool1
    {
        "attrs": [],
        "contents": [],
        "driver": "pool",
        "name": "pool1",
        "parents": []
    }
    HTTP: 200
    Content-type: application/json

Will:

#.  Create a pool entity called ``pool1``
#.  Create a basicserver entity called ``server1``
#.  Insert the entity ``server1`` into the entity ``pool1``
#.  Remove the entity ``server1`` from the entity ``pool1``

Examples:

.. code:: bash

    $ ${post} -d 'name=pool2' ${server_url}/entity/pool
    [
        "/pool/pool2"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'name=server2' -d 'name=server3' ${server_url}/entity/basicserver
    [
        "/basicserver/server2",
        "/basicserver/server3"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'device=server2' -d 'device=server3' -d 'action=insert' ${server_url}/entity/pool/pool2
    {
        "attrs": [],
        "contents": [
            "/basicserver/server2",
            "/basicserver/server3"
        ],
        "driver": "pool",
        "name": "pool2",
        "parents": []
    }
    HTTP: 200
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'device=server2' -d 'device=server3' -d 'action=remove' ${server_url}/entity/pool/pool2
    {
        "attrs": [],
        "contents": [],
        "driver": "pool",
        "name": "pool2",
        "parents": []
    }
    HTTP: 200
    Content-type: application/json

The above will:

#.  Create a pool entity called ``pool2``
#.  Create two basicserver entities called ``server2`` and ``server3``
#.  Insert both basicserver entities into the pool entity
#.  Remove both basicserver entities from the pool entity

"""

    obj, status, msg = util.get(name, driver)
    if not obj:
        return util.dumps(msg, status)
    devices = request.params.getall('device')
    action = request.params.get('action')

    if not action:
        bottle.abort(400, 'Parameter \'action\' is required.')

    devobjs = []
    notfound = []
    for device in devices:
        try:
            devobjs.append(clusto.get_by_name(device))
        except LookupError:
            notfound.append(device)

    if notfound:
        bottle.abort(404, 'Objects %s do not exist and cannot be used with "%s"' % (','.join(notfound), name,))

    if action == 'insert':
        for devobj in devobjs:
            if devobj not in obj:
                obj.insert(devobj)

    elif action == 'remove':
        for devobj in devobjs:
            if devobj in obj:
                obj.remove(devobj)

    else:
        bottle.abort(400, '%s is not a valid action.' % (action))

    return show(driver, name)
