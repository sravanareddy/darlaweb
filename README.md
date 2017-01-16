# Scripts for the DARLA server, built on the web.py framework.

## Installation 
``` 
pip install web.py inflect git+http://github.com/kylebgorman/textgrid.git celery
```
You also must install

- g2p (for OOV words in dictionary)

- mpg123 for converting mp3 -> wav files 
https://sourceforge.net/projects/mpg123/files/mpg123/

- python3 if you don't have it (and `python3 -m pip install pyyaml numpy scipy TextGrid`)

- HTK tools: [http://htk.eng.cam.ac.uk/download.shtml](http://htk.eng.cam.ac.uk/download.shtml)

	- note: if you are having trouble installing this and there is a problem with X11, use `configure --without-x --disable-hslab` so you don't need X11 (for graphing)
- R: [https://cran.cnr.berkeley.edu/](https://cran.cnr.berkeley.edu/)

-  gdata and all its dependencies here:
[https://github.com/google/gdata-python-client](https://github.com/google/gdata-python-client)  

- kitchen (for unicode parsing) here:
[https://pypi.python.org/pypi/kitchen/](https://pypi.python.org/pypi/kitchen/)

- sox
- sphinxbase and pocketsphinx: 
[sphinxbase](https://sourceforge.net/projects/cmusphinx/files/sphinxbase/5prealpha/), [pocketsphinx](https://sourceforge.net/projects/cmusphinx/files/pocketsphinx/5prealpha/)
	- read [this](http://cmusphinx.sourceforge.net/wiki/tutorialpocketsphinx) on how to download them:



## Configure and run on your computer

On Mac OS, execute main.py and preview in `http://localhost:8080/`

For cross-computer compatibility, create a file named `filepaths.json` containing a dictionary as a json file as follows:

```
{"DATA": "/absolute/path/to/directory/where/user/uploads/will/be/processed",
"PASSWORD": "/absolute/path/to/text/file/containing/the/GMail/password",
"URLBASE": "http://base.url.on.this.machine",
"ACOUSTICMODELS": /absolute/path/to/directory/withacousticmodels,
"LM": "/absolute/path/to/languagemodel",
"APPDIR": "/absolute/path/to/directory/with/applications/",
"GOOGLESPEECH": "/absolute/path/to/googleprivatekeyjson"}
```

Do *not* push `filepaths.json` to the repo, since it is dependent on the local environment.

## Restarting Lighttpd

Lighttpd does not automatically recompile the code after changes (unlike Apache), and needs to be manually restarted like so:

```
killall lighttpd
/etc/init.d/lighttpd start
```

This is only relevant for the production server.

