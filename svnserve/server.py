from gevent.server import StreamServer

class GeventSvnServer(StreamServer):
    def __init__(self, address='', port=3690, callback=None):
        super(GeventSvnServer, self).__init__((address, port), callback)
