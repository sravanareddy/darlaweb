"""class that calls alignment things """

celeryon = True  #whether or not to use celery

import web
from web import form
import myform
import utilities
import os
import sys
from featrec import featurize_recognize, align_extract

render = web.template.render('templates/', base='layout')

if celeryon:
	from celery import group

urls = {
	 '/?', 'allpipeline'
	 }

class allpipeline:
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

        edit = False  #TODO: make this a form parameter
        
        if not (os.path.isdir(os.path.join(datadir, taskname+".speakers"))):
            os.mkdir(os.path.join(datadir, taskname+".speakers"))
            os.system('chmod g+w '+os.path.join(datadir, taskname+".speakers"))

        for i in range(0, numfiles):
            i = str(i)
            filename = parameters["filename"+i]
            if filename=='ytvideo.wav':
                filename = 'ytvideo'
            try:
                o = open(os.path.join(datadir, taskname+'.speakers/converted_'+filename+'.speaker'), 'w')
                name = parameters["name"+i]
                sex = parameters["sex"+i]
                o.write('--name='+name+'\n--sex='+sex+'\n')
                o.close()
            except IOError:
                return "Error creating a job for "+filename                
	
	if celeryon:
		result = featurize_recognize.delay(os.path.join(datadir, taskname))
		while not result.ready():
			pass
		
		if result.get() == False:
			return "There was an error in processing your file - we could not extract MFCCs or run ASR."
	else:
		featurize_recognize(os.path.join(datadir, taskname))

        #editor
        if edit:
                utilities.prep_to_edit(os.path.join(datadir, taskname))
                wavfiles = sorted(filter(lambda filename: filename.endswith('wav'),
                          os.listdir(os.path.join('static', 'usersounds', taskname))))
                audiolist = []
                for wavfile in wavfiles:
                        audiolist.append(form.Textarea(wavfile[:-4], 
                                                       value=open(os.path.join('static', 'usersounds', taskname, wavfile[:-4]+'.hyp')).read(),
                                                       size="40",
                                                       description = '<audio controls><source src="{0}" type="audio/wav"></audio>'.format(os.path.join('../static', 'usersounds', taskname, wavfile))))
                transedit = myform.ListToForm(audiolist)
                return render.asredit(transedit)
        
	if celeryon:
		result = align_extract.delay(os.path.join(datadir, taskname))
		while not result.ready():
			pass
	else:
		align_extract(os.path.join(datadir, taskname))
                
	return "You may now close this window and we will email you the results. Thank you!" 

app_allpipeline = web.application(urls, locals())
