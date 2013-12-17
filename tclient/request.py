"""
tclient.request
~~~~~~~~

This module provides the Request class, which is how we build http requests.

:copyright: (c) 2013 by Rhett Garber.
:license: ISC, see LICENSE for more details.

"""
import urllib
import json

import tornado.httpclient
from tornado.escape import utf8

from .form import Form


class Request(tornado.httpclient.HTTPRequest):
    """Enhanced HTTPRequest class

    This works in a tornado httpclient context as a normal request, but has some additional magic
    that makes working with it way easier.

    You can do something like:

        req = tclient.Request('http://localhost:8887')
        req.params['search'] = 'ur mom'

    or

        req.method = "POST"
        req.body = {'name': 'Raphael'}


    And then use the request just like you would with a tornado httpclient, or through our
    own multi-fetch

        responses = tclient.fetchall([req])

    This class is also enhanced to provide an easy to use interface to form data.

        req.form['name'] = "my name"
        req.form.add_file("plan", open("~/.plan"))

    """
    def __init__(self, url, **kwargs):
        body = None
        if 'body' in kwargs:
            body = kwargs.pop('body')

        super(Request, self).__init__(None, **kwargs)

        self.url = url

        if body is not None:
            self.body = body

        self.params = {}
        self._form = None

    def get_url(self):
        url = self._url_base

        # Note we use this as a hook for doing extra 'pre-render' type operations
        if self.params:
            query = urllib.urlencode(self.params)
            if '?' in url:
                url += '&'
            else:
                url += '?'

            url += query

        return url

    @property
    def url(self):
        return self.get_url()

    @url.setter
    def url(self, value):
        self._url_base = value

    @property
    def body(self):
        if self._body is None and self._form is not None:
            self._body, self.headers['Content-Type'] = self._form.get_value()
            return self._body

        return utf8(self._body)

    @body.setter
    def body(self, value):
        if isinstance(value, dict):
            self._body = json.dumps(value)
            if 'Content-Type' not in self.headers:
                self.headers['Content-Type'] = 'application/json'
        else:
            self._body = value

    @property
    def form(self):
        if self._form is None:
            self._form = Form()
        return self._form
