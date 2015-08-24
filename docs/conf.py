#!/usr/bin/env python
#
# -*- mode:python; sh-basic-offset:4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim:set tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8:
#

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), '..')))

import clustoapi

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'Clusto API Server'
year = datetime.now().year
copyright = u'%s, %s' % (year, ','.join(dict(clustoapi.__authors__).values()),)
version = clustoapi.__branch__
release = clustoapi.__version__
exclude_patterns = ['_build']
pygments_style = 'sphinx'
if not os.environ.get('READTHEDOCS'):
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
htmlhelp_basename = 'ClustoAPIServerdoc'
latex_elements = {
}
latex_documents = [
    (
        'index', 'ClustoAPIServer.tex',
        u'Clusto API Server Documentation',
        clustoapi.__authors__[0][1], 'manual'
    ),
]
man_pages = [
    (
        'index', 'clustoapiserver',
        u'Clusto API Server Documentation',
        dict(clustoapi.__authors__).values(), 1
    )
]
texinfo_documents = [
    (
        'index', 'ClustoAPIServer', u'Clusto API Server Documentation',
        clustoapi.__authors__[0][1], 'ClustoAPIServer', clustoapi.__desc__,
        'Miscellaneous'
    ),
]
