"""edit transcriptions"""

celeryon = True

import web
from web import form
import myform
import utilities
import os
import shutil
from featrec import align_extract

if celeryon:
        from celery import group

render = web.template.render('templates/', base='layout')

urls = {
	 '/?', 'asredit'
	 }

class asredit:
        datadir = open('filepaths.txt').readline().split()[1]
	def GET(self):
                taskname = web.input()['taskname']
                #copy sound files to public
                if not os.path.exists(os.path.join('static', 'usersounds', taskname)):
                        os.mkdir(os.path.join('static', 'usersounds', taskname))
                for wavfile in os.listdir(os.path.join(self.datadir, taskname+'.audio/splits/')):
                        shutil.copyfile(os.path.join(self.datadir, 
                                                     taskname+'.audio/splits', 
                                                     wavfile),
                                        os.path.join('static',
                                                     'usersounds',
                                                     taskname,
                                                     wavfile))
                #read ASR hyps
                hyplines = map(lambda line: line.split()[:-1], 
                               open(os.path.join(self.datadir, taskname)+'.hyp').readlines())
                hyps = {}
                for line in hyplines:
                        hyps[line[-1][1:]] = line[:-1]
                #put into form to display
                wavfiles = sorted(os.listdir(os.path.join('static', 'usersounds', taskname)))
                audiolist = [form.Hidden('taskname', value=taskname)]
                for wavfile in wavfiles:
                        audiolist.append(form.Textarea(wavfile,
                                                       value=' '.join(hyps[wavfile[:-4]]),
                                                       description = '<p><audio controls><source src="{0}" type="audio/wav"></audio></p>'.format(os.path.join('../static', 'usersounds', taskname, wavfile))))
                transedit = myform.ListToForm(audiolist)
                return render.asredit(transedit)
                
        def POST(self):
                parameters = web.input()
                taskname = parameters['taskname']
                #delete audio files from public                        
                shutil.rmtree(os.path.join('static', 'usersounds', taskname))
                #write edited hyps
                hyps = filter(lambda (k,v):k.endswith('.wav'),
                              parameters.items())
                o = open(os.path.join(self.datadir, taskname+'.hyp'), 'w')
                for wavfile, transcription in hyps:
                        o.write(transcription+' ('+wavfile[:-4]+' 0)\n')
                o.close()
                
                if celeryon:
                        result = align_extract.delay(os.path.join(self.datadir, taskname))
                        while not result.ready():
                                pass
                else:
                        align_extract(os.path.join(self.datadir, taskname))
                return "You may now close this window and we will email you the formant extraction results with your corrected transcriptions. Thank you!"

app_asredit = web.application(urls, locals())
