# -*- coding: utf-8 -*-

"""
tclient
~~~~~~~~

:copyright: (c) 2013 by Rhett Garber.
:license: ISC, see LICENSE for more details.

"""

__title__ = 'tclient'
__version__ = '0.0.3'
__description__ = 'HTTP client for parallel http requests'
__url__ = 'https://github.com/rhettg/tclient'
__build__ = 0
__author__ = 'Rhett Garber'
__author_email__ = 'rhettg@gmail.com'
__license__ = 'ISC'
__copyright__ = 'Copyright 2013 Rhett Garber'


from .core import fetch_all
from .core import fetch
from .request import Request
from .utils import segment_requests

# flake8: noqa
