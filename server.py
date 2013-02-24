import socket
import time
import sys


class literal(str):
    """A unique type to distinguish between str and a literal"""
    pass

class MarshallError(Exception):
    """A Marshall error."""


class NeedMoreData(MarshallError):
    """More data needed."""

def encode(data):
    """Marshall a Python data item.

    :param x: Data item
    :return: encoded string
    """
    if isinstance(data, int):
        return "%d " % data
    elif isinstance(data, (list, tuple)):
        return "( " + "".join(map(encode, data)) + ") "
    elif isinstance(data, literal):
        return "%s " % data
    elif isinstance(data, str):
        return "%d:%s " % (len(data), data)
    elif isinstance(data, unicode):
        return "%d:%s " % (len(data), data.encode("utf-8"))
    elif isinstance(data, bool):
        if data:
            return "true "
        else:
            return "false "
    raise ValueError("Unable to marshall type %s" % repr(data))


def decode(x):
    """Unmarshall the next item from a text.

    :param x: Text to parse
    :return: tuple with unpacked item and remaining text
    """
    whitespace = ['\n', ' ']
    if len(x) == 0:
        raise NeedMoreData("Not enough data")
    if x[0] == "(": # list follows
        if len(x) <= 1:
            raise NeedMoreData("Missing whitespace")
        if x[1] != " ": 
            raise MarshallError("missing whitespace after list start")
        x = x[2:]
        ret = []
        try:
            while x[0] != ")":
                (x, n) = decode(x)
                ret.append(n)
        except IndexError:
            raise NeedMoreData("List not terminated")

        if len(x) <= 1:
            raise NeedMoreData("Missing whitespace")
        
        if not x[1] in whitespace:
            raise MarshallError("Expected space, got %c" % x[1])

        return (x[2:], ret)
    elif x[0].isdigit():
        num = ""
        # Check if this is a string or a number
        while x[0].isdigit():
            num += x[0]
            x = x[1:]
        num = int(num)

        if x[0] in whitespace:
            return (x[1:], num)
        elif x[0] == ":":
            if len(x) < num:
                raise NeedMoreData("Expected string of length %r" % num)
            return (x[num+2:], x[1:num+1])
        else:
            raise MarshallError("Expected whitespace or ':', got '%c" % x[0])
    elif x[0].isalpha():
        ret = ""
        # Parse literal
        try:
            while x[0].isalpha() or x[0].isdigit() or x[0] == '-':
                ret += x[0]
                x = x[1:]
        except IndexError:
            raise NeedMoreData("Expected literal")

        if not x[0] in whitespace:
            raise MarshallError("Expected whitespace, got %c" % x[0])

        return (x[1:], ret)
    else:
        raise MarshallError("Unexpected character '%c'" % x[0])


repos = {
    'svn://localhost/testrepo': 'ce6d8bb6-6b7a-4cb9-bf0c-f346bb840b97'
}


class Request(object):
    def __init__(self, client):
        self.client = client

    def send_and_receive(self, data, callback):
        self.send(data)
        self.read(callback)

    def send(self, data):
        data = encode(data)
        print ">>>", data
        self.client.send(data)

    def read(self, callback):
        data = self.client.recv(1024)
        print "<<<", data
        data = decode(data)
        callback(data)

    def handle(self):
        self.greeting()

    def greeting(self):
        self.send_and_receive([literal('success'), [2, 2, [], [literal('edit-pipeline')]]], self.start_auth)

    def start_auth(self, data):
        # ( success ( ( ANONYMOUS ) 36:40435d67-9594-4fb4-bb67-394e327d0cc5 ) )
        self.request_uri = data[1][2]
        self.send_and_receive([literal('success'), [[literal('ANONYMOUS')], self.get_repo_id()]], self.auth2)

    def auth2(self, data):
        # ( success ( ) )
        # ( success ( 36:40435d67-9594-4fb4-bb67-394e327d0cc5 25:svn://localhost:9630/cool ( mergeinfo ) ) )
        self.send([literal('success'), []])
        self.send_and_receive([literal('success'), [self.get_repo_id(), self.request_uri, [literal('mergeinfo')]]], self.handle_command)

    def handle_command(self, data):
        cmd, args = data[1][0], data[1][1]
        getattr(self, 'cmd_%s' % cmd.replace('-', '_'))(*args)

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
        self.send([literal('change-dir-prop'), [dir_id, 'svn:sentry:uuid', [self.get_repo_id()]]])
        self.send([literal('close-dir'), [dir_id]])
        self.send_and_receive([literal('close-edit'), []], self.handle_command)

    def cmd_success(self, *args):
        # ( success ( ) )
        self.send([literal('success'), []])
        self.end()

    def get_repo_id(self):
        return repos[self.request_uri]

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
            print
            print "listening @ svn://localhost:3690 ..."
            break
        except Exception:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.5)
    s.listen(5)
    while 1:
        req = Request(s.accept()[0])
        req.handle()
        req.end()
