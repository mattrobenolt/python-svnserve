#!/usr/bin/env python

import socket
import time
import sys

from protocol import literal, encode, decode
from objects import InMemoryRepository, SvnException, CommandNotImplemented

Repository = InMemoryRepository

# Create and register the testrepo
Repository.create('/testrepo', 'ce6d8bb6-6b7a-4cb9-bf0c-f346bb840b97')


class Request(object):
    def __init__(self, client):
        self.client = client

    def send_and_receive(self, data, callback):
        self.send(data)
        self.read(callback)

    def send(self, data):
        data = encode(data)
        self.send_raw(data)

    def send_raw(self, data):
        print("\x1b[35m>>> %s\x1b[0m" % data)
        self.client.send(data)

    def read(self, callback):
        data = self.client.recv(1024)
        print("\x1b[32m<<< %s\x1b[0m" % data)
        data = decode(data)
        try:
            callback(data)
        except SvnException as e:
            self.send_raw(str(e))
            self.end()

    def handle(self):
        self.greeting()

    def greeting(self):
        self.send_and_receive([literal('success'), [2, 2, [], [literal('edit-pipeline')]]], self.start_auth)

    def start_auth(self, data):
        # ( success ( ( ANONYMOUS ) 36:40435d67-9594-4fb4-bb67-394e327d0cc5 ) )
        self.request_uri = data[1][2]
        self.repository = Repository.get_by_uri(self.request_uri)
        self.send_and_receive([literal('success'), [[literal('ANONYMOUS')], self.repository.id]], self.auth2)

    def auth2(self, data):
        # ( success ( ) )
        # ( success ( 36:40435d67-9594-4fb4-bb67-394e327d0cc5 25:svn://localhost:9630/cool ( mergeinfo ) ) )
        self.send([literal('success'), []])
        self.send_and_receive([literal('success'), [self.repository.id, self.request_uri, [literal('mergeinfo')]]], self.handle_command)

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
        self.send([literal('success'), [[], '']])
        self.send_and_receive([literal('success'), [0]], self.handle_command)

    def cmd_reparent(self, url):
        # ( success ( ( ) 0: ) )
        # ( success ( ) )
        self.send([literal('success'), [[], '']])
        self.send_and_receive([literal('success'), []], self.handle_command)

    def cmd_check_path(self, *args):
        # ( success ( ( ) 0: ) )
        # ( success ( dir ) )
        self.send([literal('success'), [[], '']])
        self.send([literal('success'), [literal('dir')]])
        self.end()

    def cmd_update(self, *args):
        # ( success ( ( ) 0: ) )
        self.send_and_receive([literal('success'), [[], '']], self.handle_command)

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
        dir_id = 'd0'
        self.send([literal('success'), [[], '']])
        self.send([literal('target-rev'), [0]])
        self.send([literal('open-root'), [[0], dir_id]])
        self.send([literal('change-dir-prop'), [dir_id, 'svn:entry:committed-rev', ['0']]])
        self.send([literal('change-dir-prop'), [dir_id, 'svn:entry:committed-date', ['2013-01-16T01:58:37.548920Z']]])
        self.send([literal('change-dir-prop'), [dir_id, 'svn:entry:last-author', []]])
        self.send([literal('change-dir-prop'), [dir_id, 'svn:entry:uuid', [self.repository.id]]])
        self.send([literal('close-dir'), [dir_id]])
        self.send_and_receive([literal('close-edit'), []], self.handle_command)

    def cmd_success(self, *args):
        # ( success ( ) )
        self.send([literal('success'), []])
        self.end()

    def noop(self, data):
        pass

    def end(self, *args, **kwargs):
        # print "=" * 10
        self.client.close()

if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while 1:
        try:
            s.bind(('', 3690))
            print("listening @ svn://localhost:3690 ...")
            break
        except Exception:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.5)
    s.listen(5)
    while 1:
        try:
            req = Request(s.accept()[0])
        except KeyboardInterrupt:
            print("\nBye.")
            s.close()
            break
        req.handle()
        req.end()
