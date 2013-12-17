"""Code for running multiple HTTP requests via Tornado's httpclient"""
import logging
import time
import functools
import json
import urllib
import tornado.httpclient
import tornado.ioloop

try:
    import urllib3
except ImportError:
    from requests.packages import urllib3

import re

try:
    import blueox.tornado_utils
except ImportError:
    blueox = None

from tornado.escape import utf8

log = logging.getLogger(__name__)

# Hook for providing the library with a specific HTTP client. This is primarily
# for testing.
_CLIENT = None


class Form(dict):
    """Dictionary like object that handles form data.

    Note that we DO NOT support multiple values for the same name as you can for query strings.
    This is because RFC 2388 indicates you can't.
    """

    def __init__(self):
        self._files = []

    def add_file(self, file_name, file_object):
        self._files.append((file_name, file_object))

    def get_value(self, content_type=None):
        if content_type is None:
            if not self._files:
                content_type = "application/x-www-form-urlencoded"

        if (content_type is None and self._files) or (content_type and content_type.startswith("multipart/form-data")):
            fields = self.copy()
            for ndx, (file_name, file_object) in enumerate(self._files):
                fields['file_%d' % ndx] = (file_name, file_object.read())

            value, content_type = urllib3.filepost.encode_multipart_formdata(fields)
        elif content_type.startswith('application/x-www-form-urlencoded'):
            value = urllib.urlencode(self)
        elif content_type.startswith('application/json'):
            # TODO: This might be convienient
            raise NotImplementedError
        else:
            raise ValueError("Unsupported")

        return value, content_type


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

        self.base_url = url

        super(Request, self).__init__(None, **kwargs)

        if body is not None:
            self.body = body

        self.params = {}
        self._form = None

    def get_url(self):
        url = self.base_url

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
        self.url_base = value

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


def segment_requests(requests, max_bytes, max_length):
    """Split up requests so that no chunk is larger than the specified size

    Args:
        requests - list of requests to split up
        max_bytes - Maximum size for any segment of requests
        max_length - Maximum number of requests for any segment
    """

    out_chunks = []
    requests_queue = requests[:]

    current_bytes = 0
    current_chunk = []
    while requests_queue:
        req = requests_queue.pop(0)

        current_bytes += req.body and len(req.body) or 0
        current_chunk.append(req)

        if current_bytes > max_bytes or len(current_chunk) >= max_length:
            current_bytes = 0
            out_chunks.append(current_chunk)
            current_chunk = []
    else:
        if current_chunk:
            out_chunks.append(current_chunk)

    return out_chunks


def fetch_all(requests, timeout=None, retries=0):
    """Fetch all provided requests

    This function creates it's own io loop and http client to process all the requests in parallel.
    The responses are returned as a list of the exact same length.
    """
    log.debug("Starting fetch_all with %d requests", len(requests))
    if not requests:
        return []

    loop = tornado.ioloop.IOLoop()

    global _CLIENT
    if _CLIENT:
        client = _CLIENT
    elif blueox:
        client = blueox.tornado_utils.AsyncHTTPClient(io_loop=loop)
    else:
        client = tornado.httpclient.AsyncHTTPClient(io_loop=loop)

    # Since we're directly controlling our ioloop, we need to handle exceptions so we can
    # stop it in case of a failure.
    ioloop_exc = []

    def handle_exception(*exc_info):
        log.error("Exception encountered during fetch")
        loop.stop()
        ioloop_exc.append(exc_info)
        return True

    responses = [None] * len(requests)
    request_retries = [retries] * len(requests)

    def collect_response(request_ndx, response):
        log.debug("Received %d response for request %d", response.code, request_ndx)

        # Should we try again?
        if response.error and request_retries[request_ndx] > 0:
            request_retries[request_ndx] -= 1
            log.debug("Attempt %d for request %d", (retries - request_retries[request_ndx]) + 1, request_ndx)

            with tornado.stack_context.ExceptionStackContext(handle_exception):
                client.fetch(response.request, callback=functools.partial(collect_response, request_ndx))
            return

        responses[request_ndx] = response
        if all(responses):
            log.debug("Collected all responses, exiting...")
            loop.stop()

    def handle_timeout():
        log.warning("Timeout waiting on requests")
        loop.stop()

    timeout_req = None
    if timeout is not None:
        timeout_req = loop.add_timeout(time.time() + timeout, handle_timeout)

    for ndx, req in enumerate(requests):
        with tornado.stack_context.ExceptionStackContext(handle_exception):
            client.fetch(req, callback=functools.partial(collect_response, ndx))

    loop.start()

    # Did we encounter any exceptions?
    if ioloop_exc:
        exc_info = ioloop_exc[0]
        # This should re-raise the exception
        raise exc_info[0], exc_info[1], exc_info[2]

    # Cleanup
    if timeout_req is not None:
        loop.remove_timeout(timeout_req)
    client.close()
    loop.close()

    return responses


def fetch(request, timeout=None, retries=0):
    return fetch_all([request], timeout=timeout, retries=retries)[0]


class MockClient(object):
    """Simple HTTP Client Mock implementation.

    The application handler will call something like:

        resp = yield tornado.gen.Task(self.api_client, request)

    In your test fixture, you can register responses for certain calls, like:

        self.service_client.put(request, response)

    """

    def __init__(self):
        self.routes = []

    def build_response(self, request, code=200, error=None, headers={'Content-Type': 'application/json'}):
        resp = tornado.httpclient.HTTPResponse(request, code, error=error, headers=headers)
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
            log.warning("No response for %s", str(request.furl.path))
            response = self.build_response(request, code=404)

        if 'callback' in kwargs:
            kwargs['callback'](response)
        else:
            return response

    def handle(self, regex, callback):
        self.routes.append((re.compile(regex), callback))

    def close(self):
        pass


if __name__ == '__main__':
    import sys

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    req_one = Request("http://localhost:8888/test_foo", method="POST")
    req_one.form['test'] = "foo"
    req_one.form.add_file("tclient.py", open(__file__, "r"))

    requests = [
        req_one,
        tornado.httpclient.HTTPRequest("http://localhost:8887/test_bar"),
        tornado.httpclient.HTTPRequest("http://localhost:8888/test_fizz"),
        tornado.httpclient.HTTPRequest("http://localhost:8888/test_bazz"),
    ]

    request_chunks = segment_requests(requests, 1024, 2)
    assert len(request_chunks) == 3, request_chunks

    responses = []
    for chunk in request_chunks:
        responses += fetch_all(chunk, retries=2, timeout=5.0)

    for ndx, request in enumerate(requests):
        response = responses[ndx]
        if response is None:
            msg = "TIMEOUT"
        else:
            msg = response.code

        print "%d: %s %r" % (ndx, str(request.url), msg)
        print response.error
