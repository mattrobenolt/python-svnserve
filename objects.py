from urlparse import urlsplit

from protocol import literal, encode


class SvnException(Exception):
    def __init__(self, message):
        try:
            message = self.format % message
        except AttributeError:
            pass
        super(SvnException, self).__init__(message)

    def as_buffer(self):
        return [literal('failure'), [[0, self.message, '', 0]]]

    def __str__(self):
        return encode(self.as_buffer())

    __repr__ = __str__


class RepositoryDoesNotExist(SvnException):
    format = 'No repository found in %r'


class CommandNotImplemented(SvnException):
    format = 'Command not implemented: %r'


class Repository(object):
    def __init__(self, path, id):
        self.path = path
        self.id = id

    @classmethod
    def create(cls, path, id):
        raise NotImplementedError

    @classmethod
    def get_by_uri(cls, uri):
        raise NotImplementedError


class InMemoryRepository(Repository):
    repositories = {}

    def __init__(self, path, id):
        super(InMemoryRepository, self).__init__(path, id)

    @classmethod
    def create(cls, path, id):
        repo = cls(path, id)
        # register with global repos
        cls.repositories[path] = repo
        return repo

    @classmethod
    def get_by_uri(cls, uri):
        try:
            return cls.repositories[urlsplit(uri).path]
        except KeyError:
            raise RepositoryDoesNotExist(uri)
