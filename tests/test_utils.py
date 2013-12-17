from testify import (
    TestCase,
    setup,
    turtle,
    assert_equal)

from tclient import utils


class SegmentRequestsTestCase(TestCase):
    @setup
    def build_requests(self):
        self.requests = []
        for _ in range(3):
            req = turtle.Turtle(body="1")
            self.requests.append(req)

    def test_single(self):
        segments = utils.segment_requests(self.requests)
        assert_equal(len(segments), 1)
        assert_equal(len(segments[0]), 3)

    def test_max_length(self):
        segments = utils.segment_requests(self.requests, max_length=1)
        assert_equal(len(segments), len(self.requests))
        for segment in segments:
            assert_equal(len(segment), 1)

    def test_max_bytes(self):
        segments = utils.segment_requests(self.requests, max_bytes=0)
        assert_equal(len(segments), len(self.requests))
        for segment in segments:
            assert_equal(len(segment), 1)
