from testify import (
    TestCase,
    setup,
    turtle,
    assert_equal)

import json
import io

from tclient import response


class JSONTest(TestCase):
    @setup
    def build_response(self):
        self.response = response.Response(
            turtle.Turtle(),
            200,
            headers={'Content-Type': 'application/json'},
            buffer=io.StringIO(unicode(json.dumps({'value': 10}))))

    def test(self):
        assert_equal(self.response.json['value'], 10)
