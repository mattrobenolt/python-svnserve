#!/usr/bin/env sh

PID=svnserve.pid

svnserve --root . -d --foreground &
echo $! > $PID
echo "svn server running on localhost:9630"
socat -v TCP-LISTEN:9630,reuseaddr,fork TCP4:localhost:svn
kill -9 `cat $PID` && rm  $PID
