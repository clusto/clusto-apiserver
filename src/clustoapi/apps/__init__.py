#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

import os


this_dir = os.path.dirname(os.path.realpath(__file__))
__all__ = []
for f in os.listdir(this_dir):
    if f.startswith('__init__.'):
        continue
    if f.endswith('.py'):
        __all__.append(f.split('.')[0])
