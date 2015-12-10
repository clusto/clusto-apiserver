#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#
# Copyright 2010, Ron Gorodetzky <ron@parktree.net>
# Copyright 2010, Jeremy Grosser <jeremy@synack.me>
# Copyright 2013, Jorge Gallegos <kad@blegh.net>

"""
The ``ui`` application that displays clusto objects in a rich format.
"""

import os

import bottle
import clusto

from bottle import request, view, route, static_file, TemplateError
from clustoapi import util

app = bottle.Bottle()
app.config['source_module'] = __name__
bottle.TEMPLATE_PATH.insert(0, './clustoapi/apps/ui/views')

# Static content that can be overriden by #TODO
@app.route('/static/<filename:path>', name='static')
def serve_static(filename):
    return static_file(filename, root='./clustoapi/apps/ui/static')

# Base template context injection
context = dict(
    app = app,
    typelist = clusto.TYPELIST
)

def driverfinder(name):
    """ Return the driver obj of an lowercased driver named used in a URL. """
    for typename, drivers in clusto.TYPELIST.items():
        for driver in drivers:
            if name == driver.__name__.lower():
                return driver

    return clusto.drivers.Driver

@app.get('/')
@view('index')
def index():
    return context

@app.get('/<typename>', name='typeview')
def typeview(typename):
    """ Shows type view and goes back to home page if the type isn't found. """
    try:
        return bottle.template(typename, **context)
    except TemplateError as e:
        return bottle.redirect(app.get_url('/'))

@app.get('/<drivername>', name='driverview')
def driversummaries(drivername):
    """ Shows driver view and goes back to the basic driver if it isn't found. """
    context['driver'] = driverfinder(drivername)
    try:
        return bottle.template(drivername.lower(), **context)
    except TemplateError as e:
        if 'not found' in e.body:
            # I know this is a glorious assumption but it seems to work.
            drivertype = clusto.get_type_name(context['driver'])
            try
                return bottle.template('basic'+drivertype, **context)
            except TemplateError as e:
                if 'not found' in e.body:
                    return bottle.template('basicdriver', **context)
