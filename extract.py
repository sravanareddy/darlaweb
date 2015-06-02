"""class that calls alignment things """

celeryon = True  #whether or not to use celery

import web
from web import form
import myform
import utilities
import os
import sys
#script = open('scripts_directory.txt').read().strip()
#sys.path.append(script)
# sys.path.append('/home/sravana/applications/scripts/')
from featrec import just_extract

if celeryon:
	from celery import group

urls = {
	 '/?', 'extract'
	 }

class extract:
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
                print "TASKNAME " + taskname
                numfiles = int(dictionary["numfiles"])
                
                if not (os.path.isdir(taskname+".speakers")):
                        os.mkdir(taskname+".speakers")
                        os.system('chmod g+w '+(taskname+".speakers"))

                for i in range(0, numfiles):
                        i = str(i)
                        
                        filename = dictionary["filename"+i] 
                        try:
                                o = open(taskname+'.speakers/converted_'+filename+'.speaker', 'w')
                                name = dictionary["name"+i]
                                sex = dictionary["sex"+i]
                                o.write('--name='+name+'\n--sex='+sex+'\n')
                                o.close()
                        except IOError:
                                return "error creating "+filename+" for analysis."
                
                #uncelery
		if celeryon:
			result = just_extract.delay(taskname)
			while not result.ready():
				pass
		else:
			just_extract(taskname)


		return "You may now close this window and we will email you the results. Thank you!" 

app_extract = web.application(urls, locals())
