#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import bottle
import clusto
import json
import datetime


def get(name, driver=None):
    """
Tries to fetch a clusto object from a given name, optionally validating
the driver given. Returns:

 *  HTTP Error 404 if the object could not be found
 *  HTTP Error 409 if the object does not match the expected driver
 *  Clusto object otherwise
"""

    status = None
    obj = None
    msg = None
    if driver and driver not in clusto.driverlist:
        status = 412
        msg = u'The driver "%s" is not a valid driver' % (driver,)
    else:
        try:
            if driver:
                obj = clusto.get_by_name(name, assert_driver=clusto.driverlist[driver])
            else:
                obj = clusto.get_by_name(name)

        except LookupError as le:
            status = 404
            msg = u'Object "%s" not found (%s)' % (name, str(le),)

        except TypeError:
            status = 409
            msg = u'The driver for object "%s" is not "%s"' % (name, driver,)

    return obj, status, msg


def dumps(obj, code=200, headers={}):
    """
Dumps a given object as a JSON string in an HTTP Response object.
Will circumvent pretty-printing if Clusto-Minify header is True.
"""
    # Merge global response headers into the response, but do not
    # let them override the current header values.
    for header, value in bottle.response.headers.items():
        if headers.get(header) is None:
            headers[header] = value

    kwargs = {'sort_keys': True}
    headers['Clusto-Minify'] = bottle.request.headers.get('Clusto-Minify', default='False')
    if headers['Clusto-Minify'].lower() != 'true':
        kwargs['indent'] = 4
        kwargs['separators'] = (',', ': ')

    return bottle.HTTPResponse(
        json.dumps(obj, **kwargs),
        code,
        content_type='application/json',
        **headers
    )


def unclusto(obj):
    """
Convert an object to a representation that can be safely serialized into
JSON.
"""
    if type(obj) in (str, unicode, int, list, dict) or obj is None:
        return obj
    if isinstance(obj, clusto.Attribute):
        return {
            'key': obj.key,
            'value': unclusto(obj.value),
            'subkey': obj.subkey,
            'number': obj.number,
            'datatype': obj.datatype
        }
    if issubclass(obj.__class__, clusto.Driver):
        return '/%s/%s' % (obj.driver, obj.name)
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return str(obj)


def show(obj, mode=''):
    """
Will return the expanded or compact representation of a given object
"""
    if not mode:
        mode = bottle.request.headers.get('Clusto-Mode', default='expanded')

    def compact():
        return u'/%s/%s' % (obj.driver, obj.name)

    def expanded():
        result = {}
        result['name'] = obj.name
        result['driver'] = obj.driver

        attrs = []
        for x in obj.attrs():
            attrs.append(unclusto(x))
        result['attrs'] = attrs
        result['contents'] = [unclusto(x) for x in obj.contents()]
        result['parents'] = [unclusto(x) for x in obj.parents()]
        if isinstance(obj, clusto.drivers.resourcemanagers.ResourceManager):
            result['count'] = obj.count

        if 'get_ips' in dir(obj) and not obj.entity.type == 'ipmanager':
                result['ips'] = obj.get_ips()

        return result

    valid_modes = {
        'compact': compact,
        'expanded': expanded
    }
    if mode not in valid_modes:
        mode_error = '\'{0}\' is not a valid mode.'.format(mode)
        valid_mode_tip = 'Please choose from: {{{0}}}.'.format(
            ','.join(valid_modes.keys())
        )
        raise TypeError('{0} {1}'.format(mode_error, valid_mode_tip))

    return valid_modes[mode]()


def page(ents, current=1, per=50):
    """
Takes a list of entities and drops all from a list but the current page.
Returns a tuple that has the entities and also a page total so it may be
returned to the client.
"""

    first = (current - 1) * per
    last = current * per
    # 0:1 edge case with one entitiy.
    if not last:
        last = 1

    total = len(ents) / per
    total = total + 1 if len(ents) % per else 0
    return ents[first:last], total

def typecast(value, datatype, mask='%Y-%m-%dT%H:%M:%S.%f'):
    """
Takes a string and a valid clusto datatype and attempts to cast the value
to the specified datatype. Will error out if a ValueError is incurred
or a relation does not exist. Will aslo take a strptime format  as ``mask``
because typcasting datetimes is hard.
"""

    types = 'int', 'string', 'datetime', 'relation', 'json'
    if datatype not in types:
        bottle.abort(400, '%s is not a valid datatype. datatypes include: %s' % (datatype, str(types)))

    try:
        if datatype == 'int':
            return int(value)
        if datatype == 'string':
            return value
        if datatype == 'datetime':
            return datetime.datetime.strptime(value, mask)
        if datatype == 'relation':
            _, driver, name = value.split('/')
            obj, status, msg = get(name, driver=driver)
            if status > 299:
                bottle.abort(status, msg)
            return obj
        if datatype == 'json':
            return json.loads(value)
    except ValueError as ve:
        bottle.abort(400, 'Error casting %s into a(n) %s: %s' % (value, datatype, ve))
