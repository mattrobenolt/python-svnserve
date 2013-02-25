#!/usr/bin/env python

from datetime import datetime

from svnserve.protocol import literal, decode
from svnserve.responses import Response, Success
from svnserve.exceptions import SvnException, CommandNotImplemented

# Create and register the testrepo
from svnserve.objects import InMemoryRepository as Repository
Repository.create('/testrepo', 'ce6d8bb6-6b7a-4cb9-bf0c-f346bb840b97')


class Request(object):
    MAX_RECV = 1048576  # 1MB

    def __init__(self, client):
        self.client = client

    def send(self, data):
        self.send_raw(str(data))

    def send_raw(self, data):
        print("\x1b[35m>>> %s\x1b[0m" % data)
        self.client.send(data)

    def read(self, callback):
        data = self.client.recv(self.MAX_RECV + 1)
        if len(data) > self.MAX_RECV:
            self.send_and_end(SvnException('Message exceeded maximum length: {0} bytes'.format(self.MAX_RECV)))
            return

        print("\x1b[32m<<< %s\x1b[0m" % data)
        data = decode(data)
        try:
            callback(data)
        except SvnException as e:
            self.send_and_end(e)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_and_end(SvnException('Something unexepcted happened: {0!r}'.format(e)))

    def send_and_receive(self, data, callback):
        self.send(data)
        self.read(callback)

    def send_and_end(self, data):
        self.send(data)
        self.end()

    def handle(self):
        print(datetime.now().strftime('\n-- %H:%M:%S.%f --'))
        self.greeting()

    def greeting(self):
        self.send_and_receive(
            Success(2, 2, [], [literal('edit-pipeline')]),
            self.start_auth,
        )

    def start_auth(self, data):
        # ( success ( ( ANONYMOUS ) 36:40435d67-9594-4fb4-bb67-394e327d0cc5 ) )
        self.request_uri = data[1][2]
        self.repository = Repository.get_by_uri(self.request_uri)

        self.send_and_receive(
            Success([literal('ANONYMOUS')], self.repository.id),
            self.auth2
        )

    def auth2(self, data):
        # ( success ( ) )
        # ( success ( 36:40435d67-9594-4fb4-bb67-394e327d0cc5 25:svn://localhost:9630/cool ( mergeinfo ) ) )
        self.send(Success())
        self.send_and_receive(
            Success(self.repository.id, self.request_uri, [literal('mergeinfo')]),
            self.handle_command,
        )

    def handle_command(self, data):
        cmd, args = data[1][0], data[1][1]
        try:
            func = getattr(self, 'cmd_%s' % cmd.replace('-', '_'))
        except AttributeError:
            # This should be implemented on a Repository
            raise CommandNotImplemented(cmd)
        func(*args)

    def cmd_get_latest_rev(self):
        # ( success ( ( ) 0: ) )
        # ( success ( 0 ) )
        self.send(Success([], ''))
        self.send_and_receive(Success(0), self.handle_command)

    def cmd_reparent(self, url):
        # ( success ( ( ) 0: ) )
        # ( success ( ) )
        self.send(Success([], ''))
        self.send_and_receive(Success([]), self.handle_command)

    def cmd_check_path(self, *args):
        # ( success ( ( ) 0: ) )
        # ( success ( dir ) )
        self.send(Success([], ''))
        self.send_and_end(Success(literal('dir')))

    def cmd_update(self, *args):
        # ( success ( ( ) 0: ) )
        self.send_and_receive(Success([], ''), self.handle_command)

    def cmd_set_path(self, *args):
        # ( success ( ( ) 0: ) )
        # ( target-rev ( 0 ) )
        # ( open-root ( ( 0 ) 2:d0 ) )
        # ( change-dir-prop ( 2:d0 23:svn:entry:committed-rev ( 1:0 ) ) )
        # ( change-dir-prop ( 2:d0 24:svn:entry:committed-date ( 27:2013-01-16T01:58:37.548920Z ) ) )
        # ( change-dir-prop ( 2:d0 21:svn:entry:last-author ( ) ) )
        # ( change-dir-prop ( 2:d0 14:svn:entry:uuid ( 36:40435d67-9594-4fb4-bb67-394e327d0cc5 ) ) )
        # ( close-dir ( 2:d0 ) )
        # ( close-edit ( ) )
        dir_id = 'd0'  # wtf is this?
        revision = 0  # Can be any integer, not contiguous or sequential
        self.send(Success([], ''))
        self.send(Response('target-rev', revision))
        self.send(Response('open-root', [revision], dir_id))
        self.send(Response('change-dir-prop', dir_id, 'svn:entry:committed-rev', [str(revision)]))
        self.send(Response('change-dir-prop', dir_id, 'svn:entry:committed-date', ['2013-01-16T01:58:37.548920Z']))
        self.send(Response('change-dir-prop', dir_id, 'svn:entry:last-author', []))
        self.send(Response('change-dir-prop', dir_id, 'svn:entry:uuid', [self.repository.id]))
        self.send(Response('close-dir', dir_id))
        self.send_and_receive(Response('close-edit'), self.handle_command)

    def cmd_success(self, *args):
        # ( success ( ) )
        self.send_and_end(Success())

    def noop(self, data):
        pass

    def end(self, *args, **kwargs):
        self.client.close()

    @classmethod
    def accept(cls, client, address):
        req = cls(client)
        req.handle()


if __name__ == '__main__':
    from svnserve.server import GeventSvnServer
    server = GeventSvnServer(callback=Request.accept)

    try:
        print("listening @ svn://localhost:3690 ...")
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
