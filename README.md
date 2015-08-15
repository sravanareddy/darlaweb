Scripts for the DARLA server, built on the web.py framework.

# Configure on your computer

On Mac OS, execute main.py and preview in http://localhost:8080/

For cross-computer compatibility, create a file named filepaths.txt containing two lines as follows:

DATA <the absolute path to the data directory where the user data will be stored and processed>
PASSWORD <the absolute path to the text file containing the Darla GMail password>

Do NOT push this file to the repo.

# Restarting Lighttpd

Lighttpd does not automatically recompile the code after changes (unlike Apache), and needs to be manually restarted like so: 

`killall lighttpd`
`/etc/init.d/lighttpd start`



