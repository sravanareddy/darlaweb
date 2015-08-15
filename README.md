# Scripts for the DARLA server, built on the web.py framework.

## Configure on your computer

On Mac OS, execute main.py and preview in `http://localhost:8080/`

For cross-computer compatibility, create a file named `filepaths.txt` containing two lines as follows:

```
DATA /absolute/path/to/directory/where/user/uploads/will/be/stored/and/processed
PASSWORD /absolute/path/to/text/file/containing/the/GMail/password
```

Do *not* push this file to the repo.

## Restarting Lighttpd

Lighttpd does not automatically recompile the code after changes (unlike Apache), and needs to be manually restarted like so: 

```
killall lighttpd
/etc/init.d/lighttpd start
```



