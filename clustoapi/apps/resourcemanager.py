#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
# Copyright 2013, Jorge Gallegos <kad@blegh.net>

"""
The ``resourcemanager`` application will hold all methods related to resource
management in clusto. Pretty much allocating and deallocating resources.
"""

import bottle
from bottle import request
import clusto
from clusto import drivers
from clustoapi import util


app = bottle.Bottle(autojson=False)
app.config['source_module'] = __name__


def _get_resource_manager(manager, driver):
    "A wrapper because an extra check has to be made :("

    obj, status, msg = util.get(manager, driver)
    if obj:
        if not issubclass(obj.__class__, drivers.resourcemanagers.ResourceManager):
            msg = 'The object "%s" is not a resource manager' % (manager,)
            status = 409
            obj = None
        else:
            pass
    else:
        pass

    return obj, status, msg


@app.get('/')
@app.get('/<driver>')
@app.get('/<driver>/')
def list(driver=None):
    """
Lists all resource managers found in the clusto database. Optionally you can
list all resource managers that match the given ``driver``

Examples:

.. code:: bash

    $ ${post} -d 'name=zmanager' ${server_url}/resourcemanager/simplenamemanager
    {
        "attrs": [
            ...
        ],
        "contents": [],
        "count": 0,
        "driver": "simplenamemanager",
        "name": "zmanager",
        "parents": [],
        "type": "resourcemanager"
    }
    HTTP: 201
    Content-type: application/json

The above will create a simple name manager called "zmanager"

.. code:: bash

    $ ${get} ${server_url}/resourcemanager/
    [
        "/simpleentitynamemanager/testnames",
        "/simplenamemanager/zmanager"
    ]
    HTTP: 200
    Content-type: application/json

The above will list all resource managers in clusto, which should have "zmanager"

.. code:: bash

    $ ${get} ${server_url}/resourcemanager/simpleentitynamemanager
    [
        "/simpleentitynamemanager/testnames"
    ]
    HTTP: 200
    Content-type: application/json

Will list all resource managers of driver ``SimpleNameManager``

.. code:: bash

    $ ${get} ${server_url}/resourcemanager/notadriver
    "Not a valid driver \"notadriver\" (driver name notadriver doesn't exist.)"
    HTTP: 404
    Content-type: application/json

Will return a ``404`` error because that resource manager driver doesn't exist
"""

    result = []

    if driver:
        try:
            ents = clusto.get_entities(clusto_drivers=[driver])
        except NameError as ne:
            return util.dumps(
                'Not a valid driver "%s" (%s)' % (driver, ne,), 404
            )
    else:
        # Until we fix the ipmanager snafu, gotta check for both types
        ents = clusto.get_entities(clusto_types=['resourcemanager'])

    for ent in ents:
        # Kind of shitty way, but have to make sure these are all resource managers
        if issubclass(ent.__class__, drivers.resourcemanagers.ResourceManager):
            result.append(util.unclusto(ent))
    return util.dumps(result)


@app.post('/<driver>')
def create(driver):
    """
This differs from the standard way of creating entities is that resource
managers can have a number of extra parameters added to them that not
necessarily match any of the other entities. These parameters are defined
by each resource manager driver and are pretty much arbitrary. Seems like
a good idea to separate these crucial differences.

Examples:

.. code:: bash

    $ ${post} -d 'name=nameman1' ${server_url}/resourcemanager/simplenamemanager
    {
        "attrs": [
            ...
        ],
        "contents": [],
        "count": 0,
        "driver": "simplenamemanager",
        "name": "nameman1",
        "parents": [],
        "type": "resourcemanager"
    }
    HTTP: 201
    Content-type: application/json

Will create a ``SimpleNameManager`` resource manager named ``namemgr1`` with
all default values set.

.. code:: bash

    $ ${post} -d 'name=ipman1' -d 'gateway=192.168.1.1' -d 'netmask=255.255.255.0' -d 'baseip=192.168.1.10' ${server_url}/resourcemanager/ipmanager
    {
        "attrs": [
            {
                "datatype": "string",
                "key": "baseip",
                "number": null,
                "subkey": "property",
                "value": "192.168.1.10"
            },
            {
                "datatype": "string",
                "key": "gateway",
                "number": null,
                "subkey": "property",
                "value": "192.168.1.1"
            },
            {
                "datatype": "string",
                "key": "netmask",
                "number": null,
                "subkey": "property",
                "value": "255.255.255.0"
            }
        ],
        "contents": [],
        "count": 0,
        "driver": "ipmanager",
        "name": "ipman1",
        "parents": [],
        "type": "ipmanager"
    }
    HTTP: 201
    Content-type: application/json

Will create a  ``IPManager`` resource manager named ``ipman1`` with some
additional arguments such as ``netmask``, ``gateway`` and ``baseip``

"""
    if driver not in clusto.driverlist:
        return util.dumps('Requested driver "%s" does not exist' % (driver,), 412)
    cls = clusto.driverlist[driver]
    name = request.params.get('name')
    request.params.pop('name')

#   Pass any additional parameters as is to the constructor
    kwargs = {}
    for param, value in request.params.items():
        kwargs[param] = value

    found = None
    try:
        found = util.unclusto(clusto.get_by_name(name))
    except LookupError:
        pass

    obj = clusto.get_or_create(name, cls, **kwargs)

    headers = {}
    if found:
        headers['Warnings'] = 'Resource manager "%s" already exists' % (found,)

    code = 201
    if found:
        code = 202
    return util.dumps(util.show(obj), code, headers=headers)


@app.get('/<driver>/<manager>')
@app.get('/<driver>/<manager>/')
def show(driver, manager):
    """
Shows the details of the given resource manager, if it is a resource manager

Examples:

.. code:: bash

    $ ${post} -d 'name=nameman2' ${server_url}/resourcemanager/simplenamemanager
    {
        "attrs": [
            ...
        ],
        "contents": [],
        "count": 0,
        "driver": "simplenamemanager",
        "name": "nameman2",
        "parents": [],
        "type": "resourcemanager"
    }
    HTTP: 201
    Content-type: application/json

    $ ${get} ${server_url}/resourcemanager/simplenamemanager/nameman1
    {
        "attrs": [
            ...
        ],
        "contents": [],
        "count": 0,
        "driver": "simplenamemanager",
        "name": "nameman1",
        "parents": [],
        "type": "resourcemanager"
    }
    HTTP: 200
    Content-type: application/json

Will create the ``nameman2`` resource manager, then show its details. In this
case both operations yield the same data.

.. code:: bash

    $ ${get} ${server_url}/resourcemanager/simpleentitynamemanager/nonames
    "Object \"nonames\" not found (nonames does not exist.)"
    HTTP: 404
    Content-type: application/json

Will return a ``404`` error since the resource manager wasn't found

.. code:: bash

    $ ${get} ${server_url}/resourcemanager/nomanager/testnames
    "The driver \"nomanager\" is not a valid driver"
    HTTP: 412
    Content-type: application/json

Will return a ``412`` because the driver ``nomanager`` doesn't exist

.. code:: bash

    $ ${get} ${server_url}/resourcemanager/basicserver/testserver1
    "The object \"testserver1\" is not a resource manager"
    HTTP: 409
    Content-type: application/json

Will return a ``412`` instead because even though the driver ``basicserver``
exists, it is not a resource manager driver
"""

    obj, status, msg = _get_resource_manager(manager, driver)
    if not obj:
        return util.dumps(msg, status)
    else:
        return util.dumps(util.show(obj))


@app.post('/<driver>/<manager>')
def allocate(driver, manager):
    """
This allocates a new *resource* to a given *thing*. Said thing can be either
a *driver* (and the result will be a newly created object subclasses from this
driver) or an *object*, and the resource manager will allocate (bind) a
resource to it.

Examples:

.. code:: bash

    $ ${post} -d 'name=allocator' ${server_url}/resourcemanager/simpleentitynamemanager
    {
        "attrs": [
            ...
        ],
        "contents": [],
        "count": 0,
        "driver": "simpleentitynamemanager",
        "name": "allocator",
        "parents": [],
        "type": "resourcemanager"
    }
    HTTP: 201
    Content-type: application/json

    $ ${post} -d 'driver=basicserver' ${server_url}/resourcemanager/simpleentitynamemanager/allocator
    "/basicserver/01"
    HTTP: 201
    Content-type: application/json

Will request a new name from the object ``allocator`` (which is an object
of ``SimpleEntityManager`` that we just created with default values) and then
it will create a new ``BasicServer`` object.

.. code:: bash

    $ ${post} -d 'driver=basicserver' -d 'resource=99' ${server_url}/resourcemanager/simpleentitynamemanager/allocator
    "/basicserver/99"
    HTTP: 201
    Content-type: application/json

Will create a new ``BasicServer`` object from the ``testnames`` resource
manager with the specific name of ``s99``.
"""

    obj, status, msg = _get_resource_manager(manager, driver)
    if not obj:
        return util.dumps(msg, status)
    else:
        d = request.params.get('driver')
        o = request.params.get('object')
        thing = d or o
        if not thing:
            return util.dumps(
                'Cannot allocate an empty thing, send one of '
                '"driver", "object"', 404
            )
        if d:
            thing = clusto.driverlist.get(thing)
        else:
            thing = clusto.get_by_name(thing)
        if not thing:
            return util.dumps('Thing was "%s" not found' % (d or o,), 404)
        resource = request.params.get('resource', default=())
        r = obj.allocate(thing, resource)
#       The returned value can be anything such a string, number, or attribute
        return util.dumps(util.unclusto(r), 201)


@app.delete('/<driver>/<manager>')
def deallocate(driver, manager):
    """
Resource managers should allow you to deallocate *things* just the same
as allocating *things*.

Examples:

.. code:: bash

    $ ${post} -d 'name=ipman2' -d 'gateway=192.168.1.1' -d 'netmask=255.255.255.0' -d 'baseip=192.168.1.10' ${server_url}/resourcemanager/ipmanager
    {
        "attrs": [
            {
                "datatype": "string",
                "key": "baseip",
                "number": null,
                "subkey": "property",
                "value": "192.168.1.10"
            },
            {
                "datatype": "string",
                "key": "gateway",
                "number": null,
                "subkey": "property",
                "value": "192.168.1.1"
            },
            {
                "datatype": "string",
                "key": "netmask",
                "number": null,
                "subkey": "property",
                "value": "255.255.255.0"
            }
        ],
        "contents": [],
        "count": 0,
        "driver": "ipmanager",
        "name": "ipman2",
        "parents": [],
        "type": "ipmanager"
    }
    HTTP: 201
    Content-type: application/json

    $ ${post} -d 'name=names2' -d 'basename=a' ${server_url}/resourcemanager/simpleentitynamemanager
    {
        "attrs": [
            ...
        ],
        "contents": [],
        "count": 0,
        "driver": "simpleentitynamemanager",
        "name": "names2",
        "parents": [],
        "type": "resourcemanager"
    }
    HTTP: 201
    Content-type: application/json

    $ ${post} -d 'driver=basicserver' ${server_url}/resourcemanager/simpleentitynamemanager/names2
    "/basicserver/a01"
    HTTP: 201
    Content-type: application/json

    $ ${post} -d 'object=a01' ${server_url}/resourcemanager/ipmanager/ipman2
    {
        "datatype": "int",
        "key": "ip",
        "number": 0,
        "subkey": null,
        "value": 1084752130
    }
    HTTP: 201
    Content-type: application/json

    $ ${delete} -d 'object=a01' ${server_url}/resourcemanager/ipmanager/ipman2
    HTTP: 204
    Content-type:

"""

    resman, status, msg = _get_resource_manager(manager, driver)
    if not resman:
        return util.dumps(msg, status)
    else:
        obj = request.params.get('object')
        if not obj:
            return util.dumps(
                'Cannot deallocate empty, send an object to deallocate',
                404
            )
        obj, status, msg = util.get(obj)
        resource = request.params.get('resource', ())
#       Attempt to deallocate
        resman.deallocate(obj, resource=resource)
        return util.dumps(util.unclusto(resman), 204)
