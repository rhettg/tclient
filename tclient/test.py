"""
tclient.request
~~~~~~~~

This module provides tools helpful for testing with tclient

:copyright: (c) 2013 by Rhett Garber.
:license: ISC, see LICENSE for more details.

"""

import logging
import json

import tornado.httpclient
from . import fetch


log = logging.getLogger(__name__)

DEFAULT_HEADERS = {'Content-Type': 'application/json'}


def get_test_client():
    """Install and return mock http client"""
    if fetch._CLIENT is None:
        fetch._CLIENT = MockClient()

    return fetch._CLIENT


def clear_test_client():
    """Clean any installed test clients"""
    fetch._CLIENT = None


class MockClient(object):
    """Simple HTTP Client Mock implementation.

    The application handler will call something like:

        resp = yield tornado.gen.Task(self.api_client, request)

    In your test fixture, you can register responses for certain calls, like:

        self.service_client.put(request, response)

    """

    def __init__(self):
        self.routes = []

    def build_response(self, request, code=200, error=None, headers=None):
        if headers == None:
            headers = DEFAULT_HEADERS

        resp = tornado.httpclient.HTTPResponse(
            request, code, error=error, headers=headers)
        return resp

    def fetch(self, request, **kwargs):
        for reg, callback in self.routes:
            if reg.match(str(request.furl.path)):
                response_data = callback(request)

                if isinstance(response_data, str):
                    response = self.build_response(request)
                    #response.buffer = StringIO.StringIO(response_data)
                    response.buffer = "<data>"
                    response._body = response_data
                elif isinstance(response_data, dict):
                    response = self.build_response(request)
                    #response.buffer = StringIO.StringIO(json.dumps(response_data))
                    response.buffer = "<data>"
                    response._body = json.dumps(response_data)
                else:
                    response = response_data

                break
        else:
            log.warning("No response for %s", str(request.url))
            response = self.build_response(request, code=404)

        if 'callback' in kwargs:
            kwargs['callback'](response)
        else:
            return response

    def handle(self, regex, callback):
        self.routes.append((re.compile(regex), callback))

    def close(self):
        pass
