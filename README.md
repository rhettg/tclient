tclient: HTTP client for parallel http requests
=========================

TClient is an http client for doing http requests in parallel. This is really just
a light wrapper around Tornado and uses Tornado's ioloop and httpclient.


Features
--------

  * Create multiple HTTP requests, have them run in parallel.
  * Convinient API for building requests with query params, forms, or JSON.
  * Integrates with BlueOx for logging and metrics.
  * Testing hooks


Use
---

`tclient.Request` is based on `tornado.httpclient.HTTPRequest`, so you should checkout
it's [documentation](http://www.tornadoweb.org/en/stable/httpclient.html#request-objects)

In summary:

    req1 = tclient.Request('http://localhost:8888')
    req1.params['search'] = 'turtles in a half-shell'

    req2 = tclient.Request('http://localhost:8888')
    req2.method = "POST"
    req2.body = {'name': 'Raphael'}

    req3 = tclient.Request('http://localhost:8888', method="POST")
    req3.form['name'] = 'Raphael'
    req3.form.add_file("tmnt.jpg", picture_fp)

    resp1, resp2, resp3 = tclient.fetch_all([req1, req2, req3], timeout=30)
    for r in (resp1, resp2, resp3):
        r.rethrow()

    print resp1.json['results']

### Dependencies

  * tornado
  * urllib3 (just for form encoding)
  * pycurl (recommended)
  * blueox (optional)

### PyCurl

It is recommended that you enable use of PyCURL with the Tornado client. It's
just better and faster. To enable, you'd do something like:

    from tornado.httpclient import AsyncHTTPClient
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")


### Testing

We have a nice mock version of tclient you can use for testing your own applications.

    from tclient.test import get_test_client

    client = get_test_client()

    client.handle(r'/test', lambda r: client.build_response(r, body={'ok': True}))

    req = tclient.Request('http://localhost/test')
    resp = tclient.fetch(req)
    assert resp.json['ok']


Developing
----------

Want something more? Bug fix?

Developing on tclient is easy, there is even a nice Makefile to get you setup.

    make dev

This will get you a virtualenv with all the dependencies.

    make test

Run's `testify` to execute all the tests.

    make flake8

Check pep8 and flake the source code.

Make your change, send me a PR.

The project layout is based on [py-bootstrap](https://github.com/splaice/py-bootstrap)
