#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
# Copyright 2010, Ron Gorodetzky <ron@parktree.net>
# Copyright 2010, Jeremy Grosser <jeremy@synack.me>
# Copyright 2013, Jorge Gallegos <kad@blegh.net>

"""
"""

import bottle
from bottle import request
import clusto
from clustoapi import util


bottle_app = bottle.Bottle()


def _object(name, driver=None):
    """
Tries to fetch a clusto object from a given name, optionally validating
the driver given. Returns:

 *  HTTP Error 404 if the object could not be found
 *  HTTP Error 409 if the object does not match the expected driver
 *  Clusto object otherwise
"""

    try:
        if driver:
            obj = clusto.get_by_name(name, assert_driver=clusto.driverlist[driver])
        else:
            obj = clusto.get_by_name(name)

    except LookupError:
        bottle.abort(404, 'Object "%s" not found' % (name,))

    except TypeError:
        bottle.abort(409, 'The driver for object "%s" is not "%s"' % (name, driver,))

    return obj


@bottle_app.get('/')
@bottle_app.get('/<driver>')
def get_entities(driver=None):
    """
Returns all entities, or (optionally) all entities of the given driver

Example::

    curl ${server_url}/e/

Will list all entities

Example::

    curl ${server_url}/e/pool

Will list all entities that match the driver ``pool``
"""

    result = []
    kwargs = {}
    for param in request.params.keys():
        kwargs[param] = request.params.getall(param)
    if driver:
        if driver in clusto.driverlist:
            kwargs['clusto_drivers'] = [clusto.driverlist[driver]]
        else:
            bottle.abort(404, 'The requested driver "%s" does not exist' % (driver,))
    ents = clusto.get_entities(**kwargs)
    for ent in ents:
        result.append(util.unclusto(ent))
    return util.dumps(result)


@bottle_app.put('/<driver>')
def create(driver):
    """
Creates a new object of the given driver.

 *  Requires HTTP parameters ``name``

Example::

    curl -X PUT -d "name=pool1" ${server_url}/e/pool

Will create a new ``pool1`` object with a ``pool`` driver. If the
``pool1`` object already exists, this will return an error.

Example::

    curl -X PUT -d "name=pool1" -d "name=pool2" ${server_url}/e/pool

Will create new objects ``pool1`` and ``pool2`` with a ``pool`` driver. As
all objects are validated prior to creation, if any of them already exists
the entire batch operation will fail.
"""

    if driver not in clusto.driverlist:
        bottle.abort(404, 'Requested driver "%s" does not exist' % (driver,))
    cls = clusto.driverlist[driver]
    names = request.params.getall('name')
#   clean so it is not forwarded to get_entities() further down
    request.params.pop('name')

    found = []
    for name in names:
        try:
            found.append(clusto.get_by_name(name).name)
        except LookupError:
            pass

    if found:
        bottle.abort(409, 'Object(s) %s already exists' % (','.join(found),))

    for name in names:
        clusto.get_or_create(name, cls)

    return get_entities(driver)


@bottle_app.delete('/<driver>')
def delete(driver):
    """
Deletes an object if it matches the given driver

 *  Requires HTTP parameters ``name``

Example::

    curl -X DELETE -d "name=server1" ${server_url}/e/basicserver

Will create a new ``pool1`` object with a ``pool`` driver. If the
``pool1`` object already exists, this will return an error.

Example::

    curl -X PUT -d "name=pool1" -d "name=pool2" ${server_url}/e/pool

Will create new objects ``pool1`` and ``pool2`` with a ``pool`` driver. As
all objects are validated prior to creation, if any of them already exists
the entire batch operation will fail.
"""

    if driver not in clusto.driverlist:
        bottle.abort(404, 'Requested driver "%s" does not exist' % (driver,))
    names = request.params.getall('name')
#   clean so it is not forwarded to get_entities() further down
    request.params.pop('name')

    notfound = []
    objs = []
    for name in names:
        try:
            objs.append(clusto.get_by_name(name))
        except LookupError:
            notfound.append(name)

    if notfound:
        bottle.abort(404, 'Object(s) %s does not exist' % (','.join(notfound),))

    for obj in objs:
        obj.entity.delete()

    return get_entities(driver)


@bottle_app.get('/<driver>/<name>')
def show(driver, name):
    """
Returns a json representation of the given object

Example::

    curl ${server_url}/e/pool/testpool

Will return a JSON representation of the ``testpool`` object **if** its
driver is ``pool``
"""

    result = {}
    obj = _object(name, driver)

    result['name'] = name
    result['driver'] = driver

    attrs = []
    for x in obj.attrs():
        attrs.append(util.unclusto(x))
    result['attrs'] = attrs
    result['contents'] = [util.unclusto(x) for x in obj.contents()]
    result['parents'] = [util.unclusto(x) for x in obj.parents()]

    return util.dumps(result)


@bottle_app.put('/<driver>/<name>')
def insert(driver, name):
    """
Inserts the given device from the request parameters into the object

Example::

    curl -X PUT -d "device=server1" ${server_url}/e/pool/testpool

Will insert the device ``server1`` into the pool ``testpool`` **if**
the driver for ``testpool`` is ``pool``.

Example::

    curl -X PUT -d "device=server1" -d "device=server2" ${server_url}/e/pool/testpool

Will insert both objects ``server1`` and ``server2`` into the pool
``testpool``. In this example, all objects are validated before being
inserted, if any of the objects doesn't exist, the entire batch operation
will fail
"""

    obj = _object(name, driver)
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


@bottle_app.get('/<driver>/<name>/attr')
def attrs(driver, name):
    """
Query attributes from this object.

Example::

    curl ${server_url}/e/server/server1

Will show all the attributes from the object ``server1`` **if** the driver
for ``server1`` is ``server``

Example::

    curl -d "key=owner" -d "value=joe" ${server_url}/e/server/server1

Will show the attributes for ``server1`` if their key is ``owner`` *and*
the subkey is ``joe``
"""

    result = {
        'attrs': []
    }

    kwargs = dict(request.params.items())
    obj = _object(name, driver)

    for attr in obj.attrs(**kwargs):
        result['attrs'].append(util.unclusto(attr))
    return util.dumps(result)


@bottle_app.put('/<driver>/<name>/attr')
def add_attr(driver, name):
    """
Add an attribute to this object.

 *  Requires HTTP parameters ``key`` and ``value``
 *  Optional parameters are ``subkey`` and ``number``

Example::

    curl -X PUT -d "key=group" -d "value=web" ${server_url}/e/server/server1

Will add the attribute with key ``group`` with value ``web`` to the
object ``server1`` **if** the driver for ``server1`` is ``server``

Example::

    curl -X PUT -d "key=group" -d "subkey=owner" -d "value=joe" ${server_url}/e/server/server1

Will add the attribute with key ``group`` *and* subkey ``owner`` *and*
value ``joe`` to the object ``server1``
"""

    kwargs = dict(request.params.items())
    obj = _object(name, driver)
    for k in ('key', 'value'):
        if k not in kwargs.keys():
            bottle.abort(412, 'Provide at least "key" and "value"')
    if 'number' in kwargs:
        kwargs['number'] = int(kwargs['number'])
    obj.add_attr(**kwargs)
    return show(driver, name)


@bottle_app.post('/<driver>/<name>/attr')
def set_attr(driver, name):
    """
Sets an attribute from this object. If the attribute doesn't exist
it will be added, if the attribute already exists then it will be
updated.

 *  Requires HTTP parameters ``key`` and ``value``
 *  Optional parameters are ``subkey`` and ``number``

Example::

    curl -X POST -d "key=group" -d "value=web" ${server_url}/e/server/server1

Will add the attribute with key ``group`` with value ``web`` to the
object ``server1`` **if** the driver for ``server1`` is ``server``. If the
attribute already exists, it will *update* it to the value ``web``

Example::

    curl -X POST -d "key=group" -d "subkey=owner" -d "value=joe" ${server_url}/e/server/server1

Will add the attribute with key ``group`` *and* subkey ``owner`` with
value ``web`` to the object ``server1``. If the attribute already exists,
it will *update* it to the value ``joe``
"""

    kwargs = dict(request.params.items())
    obj = _object(name, driver)
    for k in ('key', 'value'):
        if k not in kwargs.keys():
            bottle.abort(412, 'Provide at least "key" and "value"')
    if 'number' in kwargs:
        kwargs['number'] = int(kwargs['number'])
    obj.set_attr(**kwargs)
    return show(driver, name)


@bottle_app.delete('/<driver>/<name>/attr')
def del_attrs(driver, name):
    """
Deletes an attribute from this object

 *  Requires HTTP parameters ``key`` and ``value``
 *  Optional parameters are ``subkey`` and ``number``

Example::

    curl -X DELETE -d "key=group" -d "value=web" ${server_url}/e/server/server1

Will detele the attribute with key ``group`` *and* value ``web`` from the
object ``server1`` **if** the driver for ``server1`` is ``server``.

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
    obj = _object(name, driver)
    if 'key' not in kwargs.keys():
        bottle.abort(412, 'Provide at least "key" and "value"')
    if 'number' in kwargs:
        kwargs['number'] = int(kwargs['number'])
    obj.del_attrs(**kwargs)
    return show(driver, name)
