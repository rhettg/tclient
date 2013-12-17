# -*- coding: utf-8 -*-

"""
tclient.utils
~~~~~~~~

This module provides utility functions that are used within Tclient
that are also useful for external consumption.

:copyright: (c) 2013 by Rhett Garber.
:license: ISC, see LICENSE for more details.

"""


def segment_requests(requests, max_bytes=None, max_length=None):
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

        if (max_bytes is not None and current_bytes > max_bytes) \
                or (max_length is not None and len(current_chunk) >= max_length):
            current_bytes = 0
            out_chunks.append(current_chunk)
            current_chunk = []
    else:
        if current_chunk:
            out_chunks.append(current_chunk)

    return out_chunks
