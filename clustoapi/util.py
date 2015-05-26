#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import bottle
import clusto
import json


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
    if type(obj) in (str, unicode, int) or obj is None:
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
