import web
from web import form
import myform
import utilities
import os
import sys
import urllib
from backend import featurize_recognize, align_extract
from hyp2mfa import asrjob_mfa, txtalignjob_mfa

render = web.template.render('templates/', base='layout')

from celery import group

urls = {
	 '/?', 'pipeline'
	 }

class pipeline:
    def GET(self):
        return render.error("That is not a valid link.", "index")

    def POST(self):
		post_list = web.data().split("&")
		parameters = {}

		for form_input in post_list:
			split = form_input.split("=")
			parameters[split[0]] = split[1]

		taskdir = urllib.unquote(parameters["taskdir"])
		job = parameters["job"]

		utilities.write_speaker_info(os.path.join(taskdir, 'speaker'), parameters["name"], parameters["sex"])

		if job == 'asr':
			result = featurize_recognize.delay(taskdir)
			while not result.ready():
				pass

			if result.get() == False:
				return render.error("There is something wrong with your audio file. We could not extract acoustic features or run ASR.", "upload/asr")

			asrjob_mfa(taskdir)

		elif job == 'txtalign':
			txtalignjob_mfa(taskdir)

		result = align_extract.delay(taskdir, confirmation_sent = (job == 'asr'))
		while not result.ready():
			pass

		return render.success('')

app_pipeline = web.application(urls, locals())
