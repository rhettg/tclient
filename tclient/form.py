"""
tclient.form
~~~~~~~~

This module provides the Form class which is a wrapper for dealing with filling
out forms for http requests.

:copyright: (c) 2013 by Rhett Garber.
:license: ISC, see LICENSE for more details.

"""
import urllib

try:
    import urllib3
except ImportError:
    from requests.packages import urllib3


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

        if (content_type is None and self._files) \
                or (content_type and content_type.startswith("multipart/form-data")):
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
