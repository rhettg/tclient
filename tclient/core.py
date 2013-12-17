"""
tclient.fetch
~~~~~~~~

This module provides the core runner for our http client.

:copyright: (c) 2013 by Rhett Garber.
:license: ISC, see LICENSE for more details.

"""
import logging
import functools
import time

import tornado.ioloop
import tornado.stack_context


try:
    import blueox.tornado_utils
except ImportError:
    blueox = None

from .response import Response


log = logging.getLogger(__name__)


# Hook for providing the library with a specific HTTP client. This is primarily
# for testing.
_CLIENT = None


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
            log.debug(
                "Attempt %d for request %d",
                (retries - request_retries[request_ndx]) + 1, request_ndx)

            with tornado.stack_context.ExceptionStackContext(handle_exception):
                client.fetch(
                    response.request,
                    callback=functools.partial(collect_response, request_ndx))

            return

        responses[request_ndx] = Response.from_response(response)
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
