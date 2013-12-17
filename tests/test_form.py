from testify import (
    TestCase,
    setup,
    teardown,
    assert_equal,
    assert_true)

from tclient.form import Form


class EmptyFormTestCase(TestCase):
    @setup
    def build_form(self):
        self.form = Form()

    def test(self):
        content, content_type = self.form.get_value()

        assert_equal(content, "")
        assert_equal(content_type, "application/x-www-form-urlencoded")


class ParamFormTestCase(TestCase):
    @setup
    def build_form(self):
        self.form = Form()
        self.form['value'] = 10
        self.form['text'] = 'A quick brown fox'

    def test(self):
        content, content_type = self.form.get_value()

        assert_equal(content, "text=A+quick+brown+fox&value=10")
        assert_equal(content_type, "application/x-www-form-urlencoded")


class FileFormTestCase(TestCase):
    @setup
    def build_form(self):
        self.form = Form()
        self.form['value'] = 10

    @setup
    def add_file(self):
        self.file = open(__file__, 'r')
        self.form.add_file(__file__, self.file)

    @teardown
    def close_file(self):
        self.file.close()

    def test(self):
        content, content_type = self.form.get_value()

        lines = content.split('\n')
        assert_true(lines[0].startswith('--'))
        assert_true(content_type.startswith("multipart/form-data"))
