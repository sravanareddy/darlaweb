"""class that calls alignment things """

celeryon = True  #whether or not to use celery

import web
from web import form
import myform
import utilities
import os
import sys
from featrec import featurize_recognize, align_extract

if celeryon:
	from celery import group

urls = {
	 '/?', 'allpipeline'
	 }

class allpipeline:
	def GET(self):
		return "TESTING"
	def POST(self):
		datadir = open('filepaths.txt').read().strip()
		post_list = web.data().split("&")
		dictionary = {}

		for form_input in post_list:
			split = form_input.split("=")
			name = split[0]
			value = split[1]
			dictionary[name] = value

		#os.chdir(datadir)
		taskname = dictionary["taskname"]
		numfiles = int(dictionary["numfiles"])
		# print "TASKNAME " + taskname
		if not (os.path.isdir(os.path.join(datadir, taskname+".speakers"))):
			os.mkdir(os.path.join(datadir, taskname+".speakers"))
			os.system('chmod g+w '+os.path.join(datadir, taskname+".speakers"))

		for i in range(0, numfiles):
			i = str(i)
			filename = dictionary["filename"+i]
                        if filename=='ytvideo.wav':
                                filename = 'ytvideo'
			try: 
				o = open(os.path.join(datadir, taskname+'.speakers/converted_'+filename+'.speaker'), 'w')
				name = dictionary["name"+i]
				sex = dictionary["sex"+i]
				o.write('--name='+name+'\n--sex='+sex+'\n')
                                o.close()
			except IOError:
				return "error creating "+filename+" for analysis."
                
		#uncelery
		if celeryon:
			result = featurize_recognize.delay(os.path.join(datadir, taskname))
			while not result.ready():
				pass
			#test if featurize_recognize works 
			if(result.get() == False):
				return "There was an error in processing your file - we could not run sphinx featurize scripts on the file."
		else:
			featurize_recognize(os.path.join(datadir, taskname))

		# #jobs = group(featurize_recognize.s(taskname, i) for i in range(numsplits))
		# #results = jobs.apply_async()
		# #while False in filter(lambda result: result.ready(), results):
		# #        pass

		#uncelery
		if celeryon:
			result = align_extract.delay(os.path.join(datadir, taskname))
			while not result.ready():
				pass
		else:
			align_extract(os.path.join(datadir, taskname))
                
		return "You may now close this window and we will email you the results. Thank you!" 

app_allpipeline = web.application(urls, locals())
