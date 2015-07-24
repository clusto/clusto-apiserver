#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
# Copyright 2010, Ron Gorodetzky <ron@parktree.net>
# Copyright 2010, Jeremy Grosser <jeremy@synack.me>
# Copyright 2013, Jorge Gallegos <kad@blegh.net>

"""
The ``attribute`` application handles all attribute specific operations like
querying, adding, deleting and updating attributes.
"""

import bottle
from bottle import request
from clustoapi import util


app = bottle.Bottle()
app.config['source_module'] = __name__


def _write_attrs(method, name, **kwargs):
    """
Helper method for reduced code between POST and PUT.
Returns a response for the methods calling it.
"""
    if method == 'set':
        code = 200
    if method == 'add':
        code = 201
    else:
        util.dumps('"%s" is neither set nor add. How did you get here?' % method, 400)

    request_kwargs = dict(request.params.items())
    driver = kwargs.get('driver', None)
    obj, status, msg = util.get(name, driver)
    if not obj:
        return util.dumps(msg, status)

    try:
        # Merge URL values and kwarg values, but do not allow conflicts.
        for k, v in request_kwargs.items():
            if kwargs.get(k) is not None and kwargs[k] != v:
                raise ValueError('Two different values were submitted for "%s": %s' % (k, [kwargs[k], v]))
            kwargs[k] = v

        # Additionally capture a value error if the json is bad.
        json_kwargs = request.json
    except ValueError as ve:
        return util.dumps('%s' % (ve,), 400)

    if json_kwargs:
        if request.query:
            return util.dumps('Error: json and query params may not be passed in the same request.', 400)
        kwargs = json_kwargs

    # Adds support for bulk attr posting.
    attrs = [kwargs] if isinstance(kwargs, dict) else kwargs
    # Check for malformed data or missing pieces before adding any attrs.
    for attr in attrs:
        for k in ('key', 'value'):
            if k not in attr.keys():
                bottle.abort(412, 'Provide at least "key" and "value"')

        if 'number' in attr:
            try:
                attr['number'] = int(attr['number'])
            except ValueError as ve:
                return util.dumps('%s' % (ve,), 400)

        if 'datatype' in attr:
            datatype = attr.pop('datatype')
            if 'mask' in attr:
                mask = attr.pop('mask', '%Y-%m-%dT%H:%M:%S.%f')
            attr['value'] = util.typecast(attr['value'], datatype, mask=mask)

    for attr in attrs:
        getattr(obj, method + '_attr')(**attr)

    return util.dumps([util.unclusto(_) for _ in obj.attrs()], code)


@app.get('/<name>')
@app.get('/<name>/')
@app.get('/<name>/<key>')
@app.get('/<name>/<key>/')
@app.get('/<name>/<key>/<subkey>')
@app.get('/<name>/<key>/<subkey>/<number:int>')
@app.get('/<name>/<key>/<subkey>/<number:int>/')
def attrs(name, key=None, subkey=None, number=None):
    """
Query attributes from this object.

Example:

.. code:: bash

    $ ${post} -d 'name=attrpool1' ${server_url}/entity/pool
    [
        "/pool/attrpool1"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${get} ${server_url}/attribute/attrpool1
    []
    HTTP: 200
    Content-type: application/json

Will show all the attributes from the object ``attrpool1``:

.. code:: bash

    $ ${get} -d 'driver=pool' ${server_url}/attribute/attrpool1
    []
    HTTP: 200
    Content-type: application/json

Will show all the attributes from the object ``attrpool1`` **if** the driver
for ``attrpool1`` is ``pool``. In the same vein this code:

.. code:: bash

    $ ${get} -d 'driver=basicserver' ${server_url}/attribute/attrpool1
    ...
    HTTP: 409
    ...

Should fail, because the ``attrpool1`` object is of type ``pool``,
**not** ``basicserver``

Example:

.. code:: bash

    $ ${get} ${server_url}/attribute/attrpool1/owner
    []
    HTTP: 200
    Content-type: application/json

Will show the attributes for ``server1`` if their key is ``owner``.
"""

    attrs = []
    kwargs = dict(request.params.items())
    driver = kwargs.get('driver', None)
    obj, status, msg = util.get(name, driver)
    if not obj:
        return util.dumps(msg, status)

    qkwargs = {}
    if key:
        qkwargs['key'] = key
    if subkey:
        qkwargs['subkey'] = subkey
    if number:
        qkwargs['number'] = number
    for attr in obj.attrs(**qkwargs):
        attrs.append(util.unclusto(attr))
    return util.dumps(attrs)


@app.post('/<name>')
@app.post('/<name>/<key>/<subkey>')
@app.post('/<name>/<key>/<subkey>/<number:int>')
def add_attr(name, **kwargs):
    """
Add an attribute to this object.

 *  Requires parameters ``name``, ``key``, and ``value``
 *  Optional parameters are ``subkey`,` ``number``, and ``datatype``
 *  Additionally, ``mask`` can be provided for a datetime attribute.
 *  These parameters can be either be passed with a querystring
 *  or a json body. If json is supplied, multiple attributes may be
 *  added at the same time.

Example:

.. code:: bash

    $ ${post} -d 'name=addattrserver' ${server_url}/entity/basicserver
    [
        "/basicserver/addattrserver"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'key=group' -d 'value=web' ${server_url}/attribute/addattrserver
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "web"
        }
    ]
    HTTP: 201
    Content-type: application/json

Will:

#.  Create an entity called ``addattrserver``
#.  Add the attribute with ``key=group`` and ``value=web`` to it

Example:

.. code:: bash

    $ ${post} -d 'key=group' -d 'subkey=owner' -d 'value=web' ${server_url}/attribute/addattrserver
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
    HTTP: 201
    Content-type: application/json

Will add the attribute with key ``group`` *and* subkey ``owner`` *and*
value ``joe`` to the previously created entity ``addattrserver``

.. code:: bash

    $ ${post} -H 'Content-Type: application/json' -d '${sample_json_attrs}' ${server_url}/attribute/addattrserver
    [
        ...
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": "admin",
            "value": "apache"
        },
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": "member",
            "value": "webapp"
        }
    ]
    HTTP: 201
    Content-type: application/json

Will add two attributes in bulk by stating
that the content type is ``application/json``.

"""

    return _write_attrs('add', name, **kwargs)


@app.put('/<name>/<key>')
@app.put('/<name>/<key>/<subkey>')
@app.put('/<name>/<key>/<subkey>/<number:int>')
def set_attr(name, **kwargs):
    """
Sets an attribute from this object. If the attribute doesn't exist
it will be added, if the attribute already exists then it will be
updated.

 *  Requires HTTP parameters ``key`` and ``value``
 *  Optional parameters are ``subkey`,` ``number``, and ``datatype``
 *  Additionally, ``mask`` can be provided for a datetime attribute.

Example:

.. code:: bash

    $ ${post} -d 'name=setattrserver' ${server_url}/entity/basicserver
    [
        "/basicserver/setattrserver"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${post} -d 'key=group' -d 'value=web' ${server_url}/attribute/setattrserver
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "web"
        }
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${put} -d 'value=db' ${server_url}/attribute/setattrserver/group
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
    Content-type: application/json

Will:

#.  Create the entity ``setattrserver``
#.  Add the attribute with ``key=group`` and ``value=web``
#.  Update the attribute to ``value=db``

Example:

.. code:: bash

    $ ${post} -d 'name=setattrserver2' ${server_url}/entity/basicserver
    [
        "/basicserver/setattrserver2"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${put} -d 'value=joe' ${server_url}/attribute/setattrserver2/group/owner
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
    Content-type: application/json

.. code:: bash

    $ ${put} -d 'value=bob' ${server_url}/attribute/setattrserver2/group/owner
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
    Content-type: application/json

Will:

#.  Create a new object ``setattrserver2`` of type ``basicserver``
#.  Set the attribute with key ``group`` *and* subkey ``owner`` with value
    ``joe`` to the object ``setattrserver1``. Since this is the only attribute
    so far, this operation works just like ``add_attr()``
#.  Update the attribute we set above, now the ``value`` will read ``bob``
"""

    return _write_attrs('set', name, **kwargs)


@app.delete('/<name>/<key>')
@app.delete('/<name>/<key>/<subkey>')
@app.delete('/<name>/<key>/<subkey>/<number:int>')
def del_attrs(name, key, subkey=None, number=None):
    """
Deletes an attribute from this object

 *  Requires HTTP path ``key``
 *  Optional parameters are ``subkey``, ``value``, and ``number``

Examples:

.. code:: bash

    $ ${post} -d 'name=deleteserver1' ${server_url}/entity/basicserver
    [
        "/basicserver/deleteserver1"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${put} -d 'value=joe' ${server_url}/attribute/deleteserver1/group/owner
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
    Content-type: application/json

.. code:: bash

    $ ${delete} ${server_url}/attribute/deleteserver1/group/owner
    []
    HTTP: 200
    Content-type: application/json

Will create a ``basicserver`` object called ``deleteserver1``, then it will
add an attribute (the only attribute so far), then it will delete it.

.. code:: bash

    $ ${post} -d 'name=deleteserver2' ${server_url}/entity/basicserver
    [
        "/basicserver/deleteserver2"
    ]
    HTTP: 201
    Content-type: application/json

.. code:: bash

    $ ${put} -d 'value=engineering' ${server_url}/attribute/deleteserver2/group
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "engineering"
        }
    ]
    HTTP: 200
    Content-type: application/json

.. code:: bash

    $ ${put} -d 'value=joe' ${server_url}/attribute/deleteserver2/group/owner
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "engineering"
        },
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": "owner",
            "value": "joe"
        }
    ]
    HTTP: 200
    Content-type: application/json

.. code:: bash

    $ ${delete} ${server_url}/attribute/deleteserver2/group/owner
    [
        {
            "datatype": "string",
            "key": "group",
            "number": null,
            "subkey": null,
            "value": "engineering"
        }
    ]
    HTTP: 200
    Content-type: application/json

This example should add two attributes with the same key, but different
subkey, then it will delete only the second value.
"""

    kwargs = dict(request.params.items())
    driver = kwargs.get('driver', None)
    obj, status, msg = util.get(name, driver)
    if not obj:
        return util.dumps(msg, status)
    qkwargs = {'key': key}
    if subkey:
        qkwargs['subkey'] = subkey
    if number:
        qkwargs['number'] = number
    obj.del_attrs(**qkwargs)
    return util.dumps([util.unclusto(_) for _ in obj.attrs()])
