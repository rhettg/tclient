from testify import (
    TestCase,
    setup,
    teardown,
    assert_equal,
    assert_raises,
    assert_true)

from tclient import core
from tclient import request
from tclient import test


class TestClientMixin(object):
    @setup
    def setup_client(self):
        self.client = test.get_test_client()

    @teardown
    def clear_client(self):
        test.clear_test_client()


class BasicTest(TestClientMixin, TestCase):
    def handle_request(self, req):
        return self.client.build_response(req)

    @setup
    def setup_handlers(self):
        self.client.handle(r'.*', self.handle_request)

    @setup
    def build_request(self):
        self.request = request.Request("/foo")

    def test(self):
        resp = core.fetch(self.request)
        assert_equal(resp.code, 200)


class FetchError(Exception):
    pass


class CatchExceptionTest(TestClientMixin, TestCase):
    """Exception catching in tornado land is kinda weird, so let's make sure
        our request handler can eventually raise an exception.
    """
    def handle_request(self, req):
        raise FetchError('here')

    @setup
    def setup_handlers(self):
        self.client.handle(r'.*', self.handle_request)

    @setup
    def build_request(self):
        self.request = request.Request("/foo")

    def test(self):
        with assert_raises(FetchError):
            core.fetch(self.request)


class TimeoutTest(TestClientMixin, TestCase):
    def handle_request(self, req):
        return None

    @setup
    def setup_handlers(self):
        self.client.handle(r'.*', self.handle_request)

    @setup
    def build_request(self):
        self.request = request.Request("/foo")

    def test(self):
        resp = core.fetch(self.request, timeout=1)
        assert_true(resp is None)


class TestRetries(TestClientMixin, TestCase):
    @setup
    def build_counter(self):
        self.calls = 0

    def handle_request(self, req):
        self.calls += 1
        return self.client.build_response(req, code=500)

    @setup
    def setup_handlers(self):
        self.client.handle(r'.*', self.handle_request)

    @setup
    def build_request(self):
        self.request = request.Request("/foo")

    def test(self):
        resp = core.fetch(self.request, retries=1)
        assert_equal(resp.code, 500)
        assert_equal(self.calls, 2)


class ParallelTest(TestClientMixin, TestCase):
    """Check that requests are actually done in parallel"""
    @setup
    def build_counter(self):
        self.calls = 0

    def handle_request(self, req):
        self.calls += 1
        # By returning None, we'll have to rely on timing out
        return None

    @setup
    def setup_handlers(self):
        self.client.handle(r'.*', self.handle_request)

    @setup
    def build_requests(self):
        self.requests = [
            request.Request("/foo"),
            request.Request("/bar"),
        ]

    def test(self):
        resp = core.fetch_all(self.requests, timeout=0.5)
        assert_equal(len(resp), 2)
        assert_equal(self.calls, 2)
