#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import shutil
import codecs
import os
from web import form
import myform
import utilities
from evaluate import run_evaluation
import asredit
import time
import json
import sys
from mturk import mturk, mturksubmit
from backend import align_extract, featurize_recognize
from formfields import make_uploadsound, make_uploadtxttrans, make_uploadboundtrans, make_email, make_delstopwords, make_delunstressedvowels, make_filterbandwidths, make_audio_validator, speaker_form
import urllib
from backend import featurize_recognize, align_extract
from hyp2mfa import asrjob_mfa, txtjob_mfa, boundjob_mfa

# [END import_libraries]

render = web.template.render('templates/', base='layout')

urls = ('/', 'index',
        '/index', 'index',
        '/cite', 'cite',
        '/about', 'about',
        '/cave', 'cave',
        '/semi', 'semi',
        '/mturk', 'mturk',
        '/stopwords', 'stopwords',
        '/mturksubmit', 'mturksubmit',
        '/upload(.+)', 'uploadjob',
        '/pipeline', 'pipeline',
        '/uploadeval', 'uploadeval',
        '/asredit', asredit.app_asredit)

app = web.application(urls, globals())
web.config.debug = True

MINDURATION = 2 # minimum uploaded audio duration in minutes

class index:
    def GET(self):
        return render.index()

class about:
    def GET(self):
        return render.about()

class cite:
    def GET(self):
        return render.cite()

class cave:
    def GET(self):
        return render.cave()

class semi:
    def GET(self):
        return render.semi()

class stopwords:
    def GET(self):
        return render.stopwords(', '.join(open('stopwords.txt').read().split()))

class uploadjob:
    uploadfile = make_uploadsound(MINDURATION)
    uploadtxtfile = make_uploadtxttrans()
    uploadboundfile = make_uploadboundtrans()
    delstopwords = make_delstopwords()
    delunstressedvowels = make_delunstressedvowels()
    filterbandwidths = make_filterbandwidths()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = make_audio_validator()

    datadir = utilities.read_filepaths()['DATA']

    def GET(self, job):
        if job == 'asr':
            formbuilder = myform.MyForm(self.uploadfile,
                                    self.delstopwords,
                                    self.delunstressedvowels,
                                    self.filterbandwidths,
                                    self.email, self.taskname, self.submit)
            pageform = formbuilder()
            return render.asrjob(pageform, "")
        elif job == 'txt':
            formbuilder = myform.MyForm(self.uploadfile,
                                           self.uploadtxtfile,
                                           self.delstopwords,
                                           self.delunstressedvowels,
                                           self.filterbandwidths,
                                           self.email, self.taskname, self.submit)
            pageform = formbuilder()
            return render.txtjob(pageform, "")
        elif job == 'bound':
            formbuilder = myform.MyForm(self.uploadfile,
                                           self.uploadboundfile,
                                           self.delstopwords,
                                           self.delunstressedvowels,
                                           self.filterbandwidths,
                                           self.email, self.taskname, self.submit)
            pageform = formbuilder()
            return render.boundjob(pageform, "")


    def POST(self, job):
        if job == 'asr':
            formbuilder = myform.MyForm(self.uploadfile,
                                    self.delstopwords,
                                    self.delunstressedvowels,
                                    self.filterbandwidths,
                                    self.email, self.taskname, self.submit,
                                    validators = self.soundvalid)
            x = web.input(uploadfile={})

        elif job == 'txt':
            formbuilder = myform.MyForm(self.uploadfile,
                                           self.uploadtxtfile,
                                           self.delstopwords,
                                           self.delunstressedvowels,
                                           self.filterbandwidths,
                                           self.email, self.taskname, self.submit)
            x = web.input(uploadfile={}, uploadtxtfile={})

        elif job == 'bound':
            formbuilder = myform.MyForm(self.uploadfile,
                                           self.uploadboundfile,
                                           self.delstopwords,
                                           self.delunstressedvowels,
                                           self.filterbandwidths,
                                           self.email, self.taskname, self.submit)
            x = web.input(uploadfile={}, uploadboundfile={})

        pageform = formbuilder()

        if job == 'txt':
            txtfilename, txtextension = utilities.get_basename(x.uploadtxtfile.filename)

            if txtextension != '.txt':  #TODO: check plaintext validity
                pageform.note = 'Upload a transcript with a .txt extension.'
                return render.txtjob(pageform, "")

        elif job == 'bound':
            boundfilename, boundextension = utilities.get_basename(x.uploadboundfile.filename)

            if boundextension != '.TextGrid':  #TODO: check textgrid validity
                pageform.note = 'Upload a TextGrid file with a .TextGrid extension.'
                return render.boundjob(pageform, "")

        if not pageform.validates(): #not validated
            if job == 'asr':
                return render.asrjob(pageform, "")
            elif job == 'txt':
                return render.txtjob(pageform, "")
            elif job == 'bound':
                return render.boundjob(pageform, "")


        #make taskname
        taskname, taskdir, error = utilities.make_task(self.datadir)
        if error!="":
            pageform.note = error
            if job == 'asr':
                return render.asrjob(pageform, "")
            elif job == 'txt':
                return render.txtjob(pageform, "")
            elif job == 'bound':
                return render.boundjob(pageform, "")

        pageform.taskname.value = taskname

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)

        if extension not in ['.wav', '.mp3']:
            pageform.note = "Please upload a .wav or .mp3 audio file."
            if job == 'asr':
                return render.asrjob(pageform, "")
            elif job == 'txt':
                return render.txtjob(pageform, "")
            elif job == 'bound':
                return render.boundjob(pageform, "")

        if job == 'asr':
            total_size, chunks, error = utilities.process_audio(taskdir,
                                                            filename,
                                                            extension,
                                                            x.uploadfile.file.read(),
                                                            dochunk=20)

            if error!="":
                pageform.note = error
                return render.asrjob(pageform, "")

            utilities.write_chunks(chunks, os.path.join(taskdir, 'chunks'))

        elif job == 'txt':
            total_size, _ , error = utilities.process_audio(taskdir,
                                                                        filename,
                                                                        extension,
                                                                        x.uploadfile.file.read(),
                                                                        dochunk=None)
            if error!="":
                pageform.note = error
                return render.txtjob(pageform, "")

            # write text transcript
            with open(os.path.join(taskdir, 'transcript.txt'), 'w') as o:
                o.write(x.uploadtxtfile.file.read())

        elif job == 'bound':
            total_size, _ , error = utilities.process_audio(taskdir,
                                                                        filename,
                                                                        extension,
                                                                        x.uploadfile.file.read(),
                                                                        dochunk=None)
            if error!="":
                pageform.note = error
                return render.boundjob(pageform, "")

            # write textgrid
            with open(os.path.join(taskdir, 'raw.TextGrid'), 'w') as o:
                o.write(x.uploadboundfile.file.read())


        if total_size < MINDURATION:
            pageform.note = "Warning: Your file totals only {:.2f} minutes of speech. We recommend at least {:.0f} minutes for best results.".format(total_size, MINDURATION)

        #generate argument files
        utilities.gen_argfiles(taskdir,
                               job,
                               filename,
                               total_size,
                               pageform.email.value,
                               pageform.delstopwords.value,
                               pageform.filterbandwidths.value,
                               pageform.delunstressedvowels.value)

        #show speaker form by adding fields to existing form and re-rendering
        speakers = speaker_form(taskdir, job)
        if job == 'asr':
            return render.asrjob(pageform, speakers)
        elif job == 'txt':
            return render.txtjob(pageform, speakers)
        elif job == 'bound':
            return render.boundjob(pageform, speakers)

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
				return render.error("There is something wrong with your audio file. We could not extract acoustic features or run ASR.", "uploadasr")

			asrjob_mfa(taskdir)

		elif job == 'txt':
			txtjob_mfa(taskdir)

		result = align_extract.delay(taskdir, confirmation_sent = (job == 'asr'))
		while not result.ready():
			pass

		return render.success('')

"""
class uploadtxttrans:
    delstopwords = make_delstopwords()
    delunstressedvowels = make_delunstressedvowels()
    filterbandwidths = make_filterbandwidths()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = make_audio_validator()

    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
        uploadtxttrans = myform.MyForm(self.uploadfile,
                                       self.uploadtxtfile,
                                       self.delstopwords,
                                       self.delunstressedvowels,
                                       self.filterbandwidths,
                                       self.email, self.taskname, self.submit)
        pageform = uploadtxttrans()
        return render.speakerstxttrans(form, "")

    def POST(self):
        uploadtxttrans = myform.MyForm(self.uploadfile,
                                       self.uploadtxtfile,
                                       self.delstopwords,
                                       self.delunstressedvowels,
                                       self.filterbandwidths,
                                       self.email, self.taskname, self.submit,
                                       validators = self.soundvalid)
        pageform = uploadtxttrans()
        x = web.input(uploadfile={}, uploadtxtfile={})

        if not pageform.validates(): #not validated
            return render.speakerstxttrans(form, "")

        txtfilename, txtextension = utilities.get_basename(x.uploadtxtfile.filename)

        if txtextension != '.txt':  #TODO: check plaintext validity
            pageform.note = 'Upload a transcript with a .txt extension.'
            return render.speakerstxttrans(form, "")

        #create new task
        taskname, audiodir, error = utilities.make_task(self.datadir)
        if error!="":
            pageform.note = error
            return render.speakerstxttrans(form, "")

        pageform.taskname.value = taskname

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)
        if extension not in ['.wav', '.mp3']:
            pageform.note = "Please upload a .wav or .mp3 file."
            return render.speakerstxttrans(form, "")
        else:
            error = utilities.write_hyp(self.datadir, taskname, filename, x.uploadtxtfile.file.read(), 'cmudict.forhtk.txt')
            if error!="":
                pageform.note = error
                return render.speakerstxttrans(form, "")

            samprate, total_size, _, error = utilities.process_audio(audiodir,
                                             filename, extension,
                    x.uploadfile.file.read(),
                dochunk=None)
            if error!="":
                form.note = error
                return render.speakerstxttrans(form, "")

        utilities.gen_argfiles(self.datadir, pageform.taskname.value, filename, 'txtalign', form.email.value, samprate, form.delstopwords.value, form.filterbandwidths.value, form.delunstressedvowels.value)

        speakers = speaker_form(filename, taskname)

        return render.speakerstxttrans(form, speakers)

class uploadboundtrans:
    uploadfile = make_uploadfile(MINDURATION)
    uploadboundfile = myform.MyFile('uploadboundfile',
                                    form.notnull,
                                    post = 'Textgrid should contain a tier named "sentence" with sentence/breath group intervals.',
                                    description='Manual transcription as a .TextGrid file:')
    delstopwords = make_delstopwords()
    delunstressedvowels = make_delunstressedvowels()
    filterbandwidths = make_filterbandwidths()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = make_audio_validator()
    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
        uploadboundtrans = myform.MyForm(self.uploadfile,
                                         self.uploadboundfile,
                                         self.delstopwords,
                                         self.delunstressedvowels,
                                         self.filterbandwidths,
                                         self.email, self.taskname, self.submit)
        form = uploadboundtrans()
        return render.speakersboundtrans(form, "")

    def POST(self):
        uploadboundtrans = myform.MyForm(self.uploadfile,
                                         self.uploadboundfile,
                                         self.delstopwords,
                                         self.delunstressedvowels,
                                         self.filterbandwidths,
                                         self.email, self.taskname, self.submit,
                                 validators = self.soundvalid)
        form = uploadboundtrans()
        x = web.input(uploadfile={}, uploadboundfile={})

        if not form.validates(): #not validated
            return render.speakersboundtrans(form, "")

        boundfilename, boundextension = utilities.get_basename(x.uploadboundfile.filename)

        if boundextension != '.textgrid':
            form.note = 'Upload a transcript with a .TextGrid extension indicating sentence boundaries.'
            return render.speakersboundtrans(form, "")

        o = codecs.open(os.path.join(self.datadir, boundfilename+boundextension), 'w', 'utf8')
        o.write(utilities.read_textupload(x.uploadboundfile.file.read()))
        o.close()

        #create new task
        taskname, audiodir, error = utilities.make_task(self.datadir)
        if error!="":
            form.note = error
            return render.speakersboundtrans(form, "")

        form.taskname.value = taskname

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)

        if extension not in ['.wav', '.mp3']:
            form.note = "Please upload a .wav or .mp3 file."
            return render.speakersboundtrans(form, "")

        chunks, error = utilities.write_sentgrid_as_lab(self.datadir, form.taskname.value, filename, boundfilename+boundextension, 'cmudict.forhtk.txt')
        if error!="":
            form.note = error
            return render.speakersboundtrans(form, "")

        samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                             filename, extension,
                    x.uploadfile.file.read(),
                    dochunk=chunks)
        if error!="":
            form.note = error
            return render.speakersboundtrans(form, "")

        utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+'.chunks'))
        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'boundalign', form.email.value, samprate, form.delstopwords.value, form.filterbandwidths.value, form.delunstressedvowels.value)

        speakers = speaker_form(filename, taskname)

        return render.speakersboundtrans(form, speakers)

class uploadtextgrid:
    uploadfile = make_uploadfile(MINDURATION)
    uploadTGfile = myform.MyFile('uploadTGfile',
                                 form.notnull,
                           post = '',
                           description='Corrected .TextGrid file')
    delstopwords = make_delstopwords()
    delunstressedvowels = make_delunstressedvowels()
    filterbandwidths = make_filterbandwidths()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = make_audio_validator()

    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
        uploadtextgrid = myform.MyForm(self.uploadfile,
                                       self.uploadTGfile,
                                       self.delstopwords,
                                       self.delunstressedvowels,
                                       self.filterbandwidths,
                                       self.email, self.taskname, self.submit,
                                       validators = self.soundvalid)
        form = uploadtextgrid()
        return render.speakerstextgrid(form, "")

    def POST(self):
        uploadtextgrid = myform.MyForm(self.uploadfile,
                                       self.uploadTGfile,
                                       self.delstopwords,
                                       self.delunstressedvowels,
                                       self.filterbandwidths,
                                       self.email, self.taskname, self.submit,
                                       validators = self.soundvalid)
        form = uploadtextgrid()
        x = web.input(uploadfile={}, uploadTGfile={})

        if not form.validates(): #not validated
            return render.speakerstextgrid(form, "")

        tgfilename, tgextension = utilities.get_basename(x.uploadTGfile.filename)

        if tgextension != '.textgrid':
            form.note = 'Upload a file with a .TextGrid extension.'
            return render.speakerstextgrid(form, "")

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)

        if extension not in ['.wav', '.mp3']:
            form.note = "Please upload a .wav or .mp3 file."
            return render.speakerstextgrid(form, "")

        #create new task
        taskname, audiodir, error = utilities.make_task(self.datadir)
        if error!="":
            form.note = error
            return render.speakerstextgrid(form, "")

        form.taskname.value = taskname

        samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                             filename, extension,
                    x.uploadfile.file.read(),
                    dochunk=None)

        if error!="":
            form.note = error
            return render.speakerstextgrid(form, "")

        utilities.write_textgrid(self.datadir, form.taskname.value, filename, utilities.read_textupload(x.uploadTGfile.file.read()))

        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'extract', form.email.value, delstopwords=form.delstopwords.value, maxbandwidth=form.filterbandwidths.value, delunstressedvowels=form.delunstressedvowels.value)

        speakers = speaker_form(filename, taskname)

        return render.speakerstextgrid(form, speakers)
"""
class uploadeval:
    reffile = myform.MyFile('reffile',
                            form.notnull,
                            post = 'Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.',
                            description='Manual transcription as plaintext .txt file:')
    hypfile = myform.MyFile('hypfile',
                            form.notnull,
                            post = '',
                            description='ASR or alternate manual transcription as plaintext .txt:')
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')
    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
            uploadeval = myform.MyForm(self.reffile,
                                       self.hypfile,
                                       self.taskname,
                                       self.submit)
            form = uploadeval()
            return render.uploadeval(form)

    def POST(self):
            uploadeval = myform.MyForm(self.reffile,
                                       self.hypfile,
                                       self.taskname,
                                       self.submit)
            form = uploadeval()

            x = web.input(reffile={}, hypfile={})

            if 'reffile' in x and 'hypfile' in x:
                    reffilename, refextension = utilities.get_basename(x.reffile.filename)
                    hypfilename, hypextension = utilities.get_basename(x.hypfile.filename)

                    if refextension!='.txt' or hypextension!='.txt':
                            form.note = 'Uploaded files must both be .txt plaintext'
                            return render.uploadeval(form)

                    taskname, _, error = utilities.make_task(self.datadir)
                    if error!="":
                        form.note = error
                        return render.uploadeval(form, "")

                    form.taskname.value = taskname

                    numreflines, numhyplines = utilities.write_transcript(self.datadir,
                                                                          taskname,
                                                                          x.reffile.file.read(),
                                                                          x.hypfile.file.read(),
                                                                          'cmudict.forhtk.txt')
                    if numreflines!=numhyplines:
                        form.note = 'Files should have the same number of lines, corresponding to each speech input. Please try again.'
                        return render.uploadeval(form)

                    evaluation = run_evaluation(self.datadir, taskname)
                    return render.evalresults(evaluation)
            else:
                    form.note = 'Please upload both transcript files.'
                    return render.uploadeval(form)

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
