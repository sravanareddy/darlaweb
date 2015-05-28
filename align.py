"""class that calls alignment things """

import web
from web import form
import myform
import utilities
import os
import sys
sys.path.append('/home/sravana/applications/scripts/')
from featrec import featurize_recognize, align_extract
from celery import group
#call from somewhere else? to keep clean - maybe move all in utilities and then utilities can call feat_rec and align_ext


urls = {
	 '/?', 'align'
	 }

class align:
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

		os.chdir(datadir)
		taskname = dictionary["taskname"]
		numfiles = int(dictionary["numfiles"])
		print "TASKNAME " + taskname
		if not (os.path.isdir(taskname+".speakers")):
			os.mkdir(taskname+".speakers")
			os.system('chmod g+w '+(taskname+".speakers"))

		# print "numfiles:"+str(numfiles)
		for i in range(0, numfiles):
			i = str(i)
			# print "value in loop: "+i
			filename = dictionary["filename"+i]
			# print "file for "+i+": "+filename
			try: 
				o = open(taskname+'.speakers/converted_'+filename+'.speaker', 'w')
				name = dictionary["name"+i]
				sex = dictionary["sex"+i]
				# location = "U"
				# age ="U"
				# ethnicity = "U"
				# years_of_schooling = "U"
				# year = "U"
				# if "location" in form: location = dictionary["location"+i]
				# if "age" in form: age = dictionary["age"+i]
				# if "ethnicity" in form: ethnicity = dictionary["ethnicity"+i]
				# if "years_of_schooling" in form: years_of_schooling = dictionary["years_of_schooling"+i]
				# if "location" in form: location = dictionary["location"+i]
				# if "year" in form: year = dictionary["year"+i]
				o.write('--name='+name+'\n--sex='+sex+'\n')
				# o.write('--name='+name+'\n--sex='+sex+'\n--location='+location+'\n--age='+age+'\n--ethnicity='+ethnicity+'\n--years_of_schooling='+years_of_schooling+'\n--year='+year)
				o.close()
			except IOError:
				return "error creating "+filename+" for analysis."

		result = featurize_recognize.delay(taskname)
		while not result.ready():
		        pass

		# #jobs = group(featurize_recognize.s(taskname, i) for i in range(numsplits))
		# #results = jobs.apply_async()
		# #while False in filter(lambda result: result.ready(), results):
		# #        pass

		result = align_extract.delay(taskname)
		while not result.ready():
		        pass

		return "You may now close this window and we will email you the results. Thank you!"

app_align = web.application(urls, locals())