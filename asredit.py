#!/usr/bin/env python                                                                        
# -*- coding: utf-8 -*- 

"""edit transcriptions"""

celeryon = True

import web
from web import form
import myform
import utilities
import os
import shutil
from featrec import align_extract
import string
import inflect

if celeryon:
        from celery import group

render = web.template.render('templates/', base='layout')

urls = {
	 '/?', 'asredit'
	 }

class asredit:
        filepaths = utilities.read_filepaths()
        datadir = filepaths['DATA']
        appdir = filepaths['APPDIR']
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
                hyps = {}
                for filename in os.listdir(os.path.join(self.datadir, taskname+'.wavlab')):
                        if filename.endswith('.lab'):
                                hyps[filename[:-4]] = open(os.path.join(self.datadir, taskname+'.wavlab', filename)).read().strip()
                #put into form to display
                wavfiles = sorted(os.listdir(os.path.join('static', 'usersounds', taskname)))
                audiolist = [form.Hidden('taskname', value=taskname)]
                for wavfile in wavfiles:
                        audiolist.append(form.Textarea(wavfile,
                                                       value=hyps[wavfile[:-4]].replace("\\'", "'"),
                                                       description = '<p><audio controls><source src="{0}" type="audio/wav"></audio></p>'.format(os.path.join('../static', 'usersounds', taskname, wavfile))))
                transedit = myform.ListToForm(audiolist)
                return render.asredit(transedit)
                
        def POST(self):
                parameters = web.input()
                taskname = parameters['taskname']
                #delete audio files from public                        
                shutil.rmtree(os.path.join('static', 'usersounds', taskname))
                #write edited labs and delete old TextGrids
                hyps = filter(lambda (k,v):k.endswith('.wav'),
                              parameters.items())
                punct = '!"#$%&\()*+,-./:;<=>?@[\\]^_`{|}~' #same as string.punct but no '
                digitconverter = inflect.engine()
                for wavfile, transcription in hyps:
                        o = open(os.path.join(self.datadir, taskname+'.wavlab', wavfile[:-4]+'.lab'), 'w')
                        transcription = transcription.replace("'", "\\'").split()
                        cleaned = map(lambda word:
                                      digitconverter.number_to_words(word).replace('-', ' ').replace(',', '') if word[0].isdigit() or (word[0]=="'" and len(word)>1 and word[1].isdigit()) else word,
                                      map(lambda word: word.lower().strip(punct), 
                                          transcription))
                        utilities.g2p(os.path.join(self.datadir, taskname), 
                                      set(cleaned), 
                                      'cmudict.forhtk.txt')
                        o.write(' '.join(cleaned)+'\n')
                        o.close()
                        if os.path.exists(os.path.join(self.datadir, taskname+'.wavlab', wavfile[:-4]+'.TextGrid')):
                                os.remove(os.path.join(self.datadir, taskname+'.wavlab', wavfile[:-4]+'.TextGrid'))
                #change task type
                filename, hmm, email, _ = open(os.path.join(self.datadir, taskname+'.alext_args')).read().split()
                o = open(os.path.join(self.datadir, taskname+'.alext_args'), 'w')
                o.write(filename+' '+hmm+' '+email+' asredit')
                o.close()
                
                #now re-run alignment and extraction
                if celeryon:
                        result = align_extract.delay(os.path.join(self.datadir, taskname), appdir)
                        while not result.ready():
                                pass
                else:
                        align_extract(os.path.join(self.datadir, taskname), appdir)
                return render.success('')
            
app_asredit = web.application(urls, locals())
