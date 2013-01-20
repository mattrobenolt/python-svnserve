import socket
import time

if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 3690))
    print "connected"
    print s.recv(1000)
    s.send('( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 24:svn://localhost/testrepo 21:SVN/1.6.18 (r1303927) ( ) ) ')
    print s.recv(1000)
