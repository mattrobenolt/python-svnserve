from .protocol import literal, encode


class SvnException(Exception):
    def __init__(self, message):
        try:
            message = self.format.format(msg=message)
        except AttributeError:
            # No special format has been specified. Ignore.
            pass
        super(SvnException, self).__init__(message)

    def as_buffer(self):
        return [literal('failure'), [[0, self.message, '', 0]]]

    def __str__(self):
        return encode(self.as_buffer())

    __repr__ = __str__


class RepositoryDoesNotExist(SvnException):
    format = 'No repository found in {msg!r}'


class CommandNotImplemented(SvnException):
    format = 'Command not implemented: {msg!r}'
