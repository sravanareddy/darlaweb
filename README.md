Scripts for the DARLA server with web.py and lighttpd.

CONFIGURATION:

On Mac OS, execute main.py and preview in http://localhost:8080/

For cross-computer compatibility, create a file named filepaths.txt -- which is read by main.py -- containing the absolute path to the "uploads" data directory. (Do not push this file to the repo.)

To stop and start lighttpd: 

killall lighttpd
/etc/init.d/lighttpd start

