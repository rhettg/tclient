import json

from tornado import httpclient


class Response(httpclient.HTTPResponse):
    @property
    def json(self):
        try:
            return self._json
        except AttributeError:
            self._json = json.loads(self.body)
            return self._json

    @classmethod
    def from_response(self, response):
        return Response(response.request, response.code,
                        headers=response.headers,
                        buffer=response.buffer,
                        effective_url=response.effective_url,
                        error=response.error,
                        request_time=response.request_time,
                        time_info=response.time_info,
                        reason=response.reason)
