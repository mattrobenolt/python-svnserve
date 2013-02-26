from .protocol import literal, encode

__all__ = ('Response', 'Success')


class BaseResponse(object):
    def __init__(self, *args):
        assert hasattr(self, 'name')
        self.args = args
        super(BaseResponse, self).__init__()

    def as_buffer(self):
        return [literal(self.name), self.args]

    def __str__(self):
        return encode(self.as_buffer())


class Response(BaseResponse):
    def __init__(self, name, *args):
        self.name = name
        super(Response, self).__init__(*args)


class Success(BaseResponse):
    name = 'success'
