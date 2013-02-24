from urlparse import urlsplit

class Repository(object):
    def __init__(self, path, id):
        self.path = path
        self.id = id


repositories = {}
class InMemoryRepository(Repository):
    def __init__(self, path, id):
        super(InMemoryRepository, self).__init__(path, id)
        # register with global repos
        repositories[path] = self


def get_by_uri(uri):
    return repositories[urlsplit(uri).path]
