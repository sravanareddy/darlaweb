"""class that calls alignment things """

celeryon = True  #whether or not to use celery

import web
from web import form
import myform
import utilities
import os
import sys
from featrec import align_extract

render = web.template.render('templates/', base='layout')

if celeryon:
	from celery import group

urls = {
	 '/?', 'extract'
	 }

class extract:
	def GET(self):
		return render.error("That is not a valid link.", "uploadtextgrid")
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
			utilities.write_speaker_info(os.path.join(datadir, taskname+'.speakers/converted_'+filename+'.speaker'), parameters["name"], parameters["sex"])
		except IOError:
			return render.error("There was an error processing "+filename, "uploadtextgrid")

		if celeryon:
			result = align_extract.delay(os.path.join(datadir, taskname))
			while not result.ready():
				pass
		else:
			align_extract(os.path.join(datadir, taskname))

		return render.success('')

app_extract = web.application(urls, locals())
