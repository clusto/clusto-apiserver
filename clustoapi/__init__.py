#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

__major__ = 0
__minor__ = 3
__release__ = 2
__dotbranch__ = (__major__, __minor__,)
__branch__ = u'.'.join([u'%s' % (_,) for _ in __dotbranch__])
__dotversion__ = (__major__, __minor__, __release__,)
__version__ = u'.'.join([u'%s' % (_,) for _ in __dotversion__])
__desc__ = u'RESTful API server to interact with the clusto database.'
__authors__ = [
    (u'kad@blegh.net', u'Jorge Gallegos')
]
