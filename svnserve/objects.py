from urlparse import urlsplit

from .exceptions import RepositoryDoesNotExist


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
