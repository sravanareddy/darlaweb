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
	 '/?', 'alignextract'
	 }

class alignextract:
	def GET(self):
		return render.error("That is not a valid link.", "semi")
    
	def POST(self):
		datadir = open('filepaths.txt').readline().split()[1]
		post_list = web.data().split("&")
		parameters = {}

		for form_input in post_list:
			split = form_input.split("=")
			parameters[split[0]] = split[1]

		taskname = parameters["taskname"]
		        
		if not (os.path.isdir(os.path.join(datadir, taskname+".speakers"))):
			os.mkdir(os.path.join(datadir, taskname+".speakers"))
			os.system('chmod g+w '+os.path.join(datadir, taskname+".speakers"))

		filename = parameters["filename"]
		if filename=='ytvideo.wav':
			filename='ytvideo'

		try:
			o = open(os.path.join(datadir, taskname+'.speakers/converted_'+filename+'.speaker'), 'w')
			name = parameters["name"]
			sex = parameters["sex"]
			o.write('--name='+name+'\n--sex='+sex+'\n')
			o.close()
		except IOError:
			return render.error("Error creating a job for {0}.".format(filename), "index.html")
                
		if celeryon:
			result = align_extract.delay(os.path.join(datadir, taskname))
			while not result.ready():
				pass
		else:
			align_extract(os.path.join(datadir, taskname))

		return render.success()
    
app_alignextract = web.application(urls, locals())
