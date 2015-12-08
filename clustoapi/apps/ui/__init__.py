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
from bottle import request, view, route, static_file
from clustoapi import util

app = bottle.Bottle()
app.config['source_module'] = __name__
bottle.TEMPLATE_PATH.insert(0, './clustoapi/apps/ui/views')

@app.route('/static/<filename:path>',name='static',method='GET')
def serve_static(filename):
    print filename
    return static_file(filename,root='./clustoapi/apps/ui/static')

@app.get('/')
@view('index')
def index():
    return dict(app = app)
