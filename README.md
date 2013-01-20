# svnserve
## Goals
 * Write a faux svn server that emulates enough of the svn protocol to write applications
 * Pluggable data backends
  * Database, Redis, CouchDB, etc.

## Why am I doing this?
I think the svn protocol can be a good venue for generic file storage. I feel like many different thing could take advantage of an svn interface.

 * Access to latest updates from an HTTP api
  * Maybe `svn up` from Basecamp to get the latest files?
 * Present CouchDB versioned data over svn
 * Shove this svn layer in front of a normal HTTP directory and pull updates by checking last-modified timestamps
 * emulate a file system in a database
 * **anything that has data that updates**

![](http://i2.kym-cdn.com/photos/images/original/000/234/786/bf7.gif)
