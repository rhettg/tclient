from testify import (
    TestCase,
    setup,
    assert_equal,
    assert_true)

import urlparse
from tclient import request


class BasicTestCase(TestCase):
    @setup
    def build_request(self):
        self.request = request.Request("http://localhost:8888")

    def test(self):
        url = self.request.url
        assert_equal(url, "http://localhost:8888")

        body = self.request.body
        assert_true(body is None)


class SetURLTestCase(TestCase):
    @setup
    def build_request(self):
        self.request = request.Request("http://localhost:8888")
        self.request.url = "http://github.com/rhettg"

    def test(self):
        url = self.request.url
        assert_equal(url, "http://github.com/rhettg")


class SetURLwParamsTestCase(TestCase):
    """Just a check to ensure our property isn't getting wiped out"""
    @setup
    def build_request(self):
        self.request = request.Request("http://localhost:8888")
        self.request.url = "http://github.com/rhettg"
        self.request.params['foo'] = 'bar'

    def test(self):
        url = self.request.url
        assert_equal(url, "http://github.com/rhettg?foo=bar")


class ParamsTestCase(TestCase):
    @setup
    def build_request(self):
        self.request = request.Request("http://localhost:8888")
        self.request.params['f'] = 1
        self.request.params['query'] = 'a sentence'

    def test(self):
        url = self.request.url
        parse_url = urlparse.urlparse(url)
        assert_equal(parse_url.netloc, 'localhost:8888')

        query = urlparse.parse_qs(parse_url.query)
        assert_equal(query['f'][0], '1')
        assert_equal(query['query'][0], 'a sentence')


class RawBodyTestCase(TestCase):
    @setup
    def build_request(self):
        self.body = "Hello world"
        self.request = request.Request("http://localhost:8888", method="POST")
        self.request.body = self.body

    def test(self):
        assert_equal(self.request.body, self.body)


class JSONBodyTestCase(TestCase):
    @setup
    def build_request(self):
        self.msg = "Hello world"
        self.request = request.Request("http://localhost:8888", method="POST")
        self.request.body = {'msg': self.msg}

    def test(self):
        assert_equal(self.request.body, '{"msg": "Hello world"}')
        assert_equal(self.request.headers['Content-Type'], 'application/json')
