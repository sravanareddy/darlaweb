"""class that calls alignment things """

celeryon = True  #whether or not to use celery

import web
from web import form
import myform
import utilities
import os
import sys
from featrec import align_extract

if celeryon:
	from celery import group

urls = {
	 '/?', 'extract'
	 }

class extract:
	def GET(self):
		return "Invalid"
	def POST(self):
		datadir = open('filepaths.txt').readline().split()[1]
		post_list = web.data().split("&")
		parameters = {}

		for form_input in post_list:
			split = form_input.split("=")
			parameters[split[0]] = split[1]

                taskname = parameters["taskname"]
                numfiles = int(parameters["numfiles"])
                
                if not (os.path.isdir(os.path.join(datadir, taskname+".speakers"))):
                        os.mkdir(os.path.join(datadir, taskname+".speakers"))
                        os.system('chmod g+w '+os.path.join(datadir, taskname+".speakers"))

                for i in range(0, numfiles):
                        i = str(i)
                        
                        filename = parameters["filename"+i]
                        if filename=='ytvideo.wav':
                                filename='ytvideo'
                        try:
                                o = open(os.path.join(datadir, taskname+'.speakers/converted_'+filename+'.speaker'), 'w')
                                name = parameters["name"+i]
                                sex = parameters["sex"+i]
                                o.write('--name='+name+'\n--sex='+sex+'\n')
                                o.close()
                        except IOError:
                                return "error creating "+filename+" for analysis."
                
		if celeryon:
			result = align_extract.delay(os.path.join(datadir, taskname))
			while not result.ready():
				pass
		else:
			align_extract(os.path.join(datadir, taskname))
		
		return "You may now close this window and we will email you the results. Thank you!" 

app_extract = web.application(urls, locals())
