#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
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
import shlex
from mturk import mturk, mturksubmit
from backend import align_extract, azure_transcription, featurize_recognize, bedword_transcription
from formfields import make_uploadsound, make_uploadtxttrans, make_uploadboundtrans, make_uploadtgtrans, \
    make_email, make_delstopwords, make_delunstressedvowels, make_filterbandwidths, \
        make_audio_validator, speaker_form, make_format_checkbox, make_diarize, make_punctuate, make_send_to_darla
import urllib
from backend import featurize_recognize, align_extract
from hyp2mfa import asrjob_mfa, azurejob_mfa, txtjob_mfa, boundjob_mfa

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
        '/cmudict', 'cmudict',
        '/mturksubmit', 'mturksubmit',
        '/upload(.+)', 'uploadjob',
        '/pipeline', 'pipeline',
        '/asreval', 'asreval',
        '/bedword', 'bedword')

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

class cmudict:
    def GET(self):
        return render.cmudict(open('cmudict.stress.txt').readlines())

class uploadjob:
    uploadfile = make_uploadsound(MINDURATION)
    uploadtxtfile = make_uploadtxttrans()
    uploadboundfile = make_uploadboundtrans()
    uploadtgfile = make_uploadtgtrans()
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
        elif job == 'azure':
            formbuilder = myform.MyForm(self.uploadfile,
                                    self.delstopwords,
                                    self.delunstressedvowels,
                                    self.filterbandwidths,
                                    self.email, self.taskname, self.submit)
            pageform = formbuilder()
            return render.azurejob(pageform, "")
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
        elif job == 'extract':
            formbuilder = myform.MyForm(self.uploadfile,
                                           self.uploadtgfile,
                                           self.delstopwords,
                                           self.delunstressedvowels,
                                           self.filterbandwidths,
                                           self.email, self.taskname, self.submit)
            pageform = formbuilder()
            return render.extractjob(pageform, "")


    def POST(self, job):
        if job == 'asr' or job == 'azure':
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

        elif job == 'extract':
            formbuilder = myform.MyForm(self.uploadfile,
                                           self.uploadtgfile,
                                           self.delstopwords,
                                           self.delunstressedvowels,
                                           self.filterbandwidths,
                                           self.email, self.taskname, self.submit)
            x = web.input(uploadfile={}, uploadtgfile={})

        pageform = formbuilder()

        if job == 'txt':
            txtfilename, txtextension = utilities.get_basename(x.uploadtxtfile.filename)

            if txtextension != '.txt':  #TODO: check plaintext validity
                pageform.note = 'Upload a transcript with a .txt extension.'
                return render.txtjob(pageform, "")

        elif job == 'bound':
            boundfilename, boundextension = utilities.get_basename(x.uploadboundfile.filename)
            if boundextension != '.textgrid':  #TODO: check textgrid validity
                pageform.note = 'Upload a TextGrid file with a .TextGrid extension.'
                return render.boundjob(pageform, "")

        elif job == 'extract':
            tgfilename, tgextension = utilities.get_basename(x.uploadtgfile.filename)
            if tgextension != '.textgrid':  #TODO: check textgrid validity
                pageform.note = 'Upload a TextGrid file with a .TextGrid extension.'
                return render.extractjob(pageform, "")

        if not pageform.validates(): #not validated
            if job == 'asr':
                return render.asrjob(pageform, "")
            elif job == 'azure':
                return render.azurejob(pageform, "")
            elif job == 'txt':
                return render.txtjob(pageform, "")
            elif job == 'bound':
                return render.boundjob(pageform, "")
            elif job == 'extract':
                return render.extractjob(pageform, "")

        #make taskname
        taskname, taskdir, error = utilities.make_task(self.datadir)
        if error!="":
            pageform.note = error
            if job == 'asr':
                return render.asrjob(pageform, "")
            elif job == 'azure':
                return render.azurejob(pageform, "")
            elif job == 'txt':
                return render.txtjob(pageform, "")
            elif job == 'bound':
                return render.boundjob(pageform, "")
            elif job == 'extract':
                return render.extractjob(pageform, "")

        pageform.taskname.value = taskname

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)

        if extension not in ['.wav', '.mp3']:
            pageform.note = "Please upload a .wav or .mp3 audio file."
            if job == 'asr':
                return render.asrjob(pageform, "")
            elif job == 'azure':
                return render.azurejob(pageform, "")
            elif job == 'txt':
                return render.txtjob(pageform, "")
            elif job == 'bound':
                return render.boundjob(pageform, "")
            elif job == 'extract':
                return render.extractjob(pageform, "")

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
        
        elif job == 'azure':
            total_size, chunks, error = utilities.process_audio(taskdir,
                filename,
                extension,
                x.uploadfile.file.read(),
                dochunk=570,
            )

            if error!="":
                pageform.note = error
                return render.azurejob(pageform, "")

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

        elif job == 'extract':
            total_size, _ , error = utilities.process_audio(taskdir,
                                                                        filename,
                                                                        extension,
                                                                        x.uploadfile.file.read(),
                                                                        dochunk=None)
            if error!="":
                pageform.note = error
                return render.extractjob(pageform, "")

            # write textgrid
            with open(os.path.join(taskdir, 'raw.TextGrid'), 'w') as o:
                o.write(x.uploadtgfile.file.read())


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
        elif job == 'azure':
                return render.azurejob(pageform, speakers)
        elif job == 'txt':
            return render.txtjob(pageform, speakers)
        elif job == 'bound':
            return render.boundjob(pageform, speakers)
        elif job == 'extract':
            return render.extractjob(pageform, speakers)

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

        elif job == 'azure':
            result = azure_transcription.delay(taskdir)
            while not result.ready():
                pass

            if result.get() == False:
                return render.error("There is something wrong with your audio file. We could not extract acoustic features or run ASR.", "uploadazure")

            azurejob_mfa(taskdir)

        elif job == 'txt':
            txtjob_mfa(taskdir)

        elif job == 'bound':
            boundjob_mfa(taskdir)

        result = align_extract.delay(taskdir, confirmation_sent = (job == 'asr' or job == 'azure'))
        while not result.ready():
            pass

        return render.success('')

class asreval:
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
            return render.asreval(form)

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
                                                                          'cmudict.nostress.txt')
                    if numreflines!=numhyplines:
                        form.note = 'Files should have the same number of lines, corresponding to each speech input. Please try again.'
                        return render.uploadeval(form)

                    evaluation = run_evaluation(self.datadir, taskname)
                    return render.evalresults(evaluation)
            else:
                    form.note = 'Please upload both transcript files.'
                    return render.asreval(form)

class bedword:
    upload_api_key = form.Textbox('api_key', form.notnull,
            form.regexp(r'^[A-Za-z0-9_-]*$', 'Please enter a valid Deepgram API Key.'),
            post='You can access your API Key from your Deepgram account.',
            description='Deepgram API Key:')
    upload_audio_file = myform.MyFile('audio_file', description='Audio file:')
    diarize_selection = make_diarize()
    punctuate_selection = make_punctuate()

    # For now, we decided that it just makes sense to email all output formats rather than
    # have the users select which ones they want. If this decision changes in the future, feel
    # free to uncomment the relevant lines below
    
    # textgrid_format = make_format_checkbox('.TextGrid')
    # csv_format = make_format_checkbox('.csv')
    # txt_format = make_format_checkbox('.txt')
    # eaf_format = make_format_checkbox('.eaf')
    send_to_darla = make_send_to_darla()
    stop_words = make_delstopwords()
    unstressed_vowels = make_delunstressedvowels()
    bandwidths = make_filterbandwidths()
    speaker_type = myform.MyRadio('sex', [('M','Low ', 'M'), ('F','High ', 'F')], description='Voice type: ')
    speaker_type.value = 'M'  # default if not checked
    upload_email = make_email()
    submit = form.Button('submit', type='submit', description='Submit')

    def GET(self):
        # TODO: make web form pretty
        builder = myform.MyForm(self.upload_api_key,
                                self.upload_audio_file,
                                self.diarize_selection,
                                self.punctuate_selection,
                                # self.textgrid_format,
                                # self.csv_format,
                                # self.txt_format,
                                # self.eaf_format,
                                self.send_to_darla,
                                self.stop_words,
                                self.unstressed_vowels,
                                self.bandwidths,
                                self.speaker_type,
                                self.upload_email,
                                self.submit)
        pageform = builder()
        return render.bedword(pageform)

    def POST(self):
        builder = myform.MyForm(self.upload_api_key,
                                self.upload_audio_file,
                                self.diarize_selection,
                                self.punctuate_selection,
                                # self.textgrid_format,
                                # self.csv_format,
                                # self.txt_format,
                                # self.eaf_format,
                                self.send_to_darla,
                                self.stop_words,
                                self.unstressed_vowels,
                                self.bandwidths,
                                self.speaker_type,
                                self.upload_email,
                                self.submit)
        pageform = builder()

        # clean input and get form values
        if not pageform.validates():
            return render.bedword(pageform)

        api_key = pageform.api_key.value
        diarize = pageform.diarize.value == 'Y'
        punctuate = pageform.diarize.value == 'Y'
        # output_formats = []
        # for format in ['.TextGrid', '.csv', '.txt', '.eaf']:
        #     if pageform[format].value == 'Y':
        #         output_formats.append(format)
        # if len(output_formats) == 0:
        #     pageform.note = 'Please select at least one output format.'
            # return render.bedword(pageform)
        output_formats = ['.TextGrid', '.csv', '.txt', '.eaf']
        send_to_darla = pageform.send_to_darla.value == 'Y'
        delstopwords = pageform.delstopwords.value
        maxbandwidth = pageform.filterbandwidths.value
        delunstressedvowels = pageform.delunstressedvowels.value
        sex = pageform.sex.value
        email = pageform.email.value
        
        # generate backend task dir and accessory files
        datadir = utilities.read_filepaths()['DATA']
        taskname, taskdir, error = utilities.make_task(datadir)

        if error != "":
            pageform.note = error
            return render.bedword(pageform)

        print(taskdir)

        # validate api_key by running validate_deepgram_key.py
        # we have to do this in a child process because the deepgram API needs python3
        # and this code is being run in python2. The child process will create a file in
        # taskdir that tells us if the key is valid or not
        args = ' '.join(['python3', './validate_deepgram_key.py', taskdir, api_key])
        key_validation = subprocess.Popen(shlex.split(args))
        retval = key_validation.wait()

        if retval != 0:
            pageform.note = 'Please enter a valid Deepgram API Key.'
            return render.bedword(pageform)

        x = web.input(audio_file={})

        filename, extension = utilities.get_basename(x.audio_file.filename)

        if extension not in ['.wav', '.mp3']:
            pageform.note = "Please upload a .wav or .mp3 audio file."
            return render.bedword(pageform)
        
        total_size, _, error = utilities.process_audio(taskdir,
                                                            filename,
                                                            extension,
                                                            x.audio_file.file.read(),
                                                            dochunk=None)

        audio_length = total_size * 60.0

        if error != "":
            pageform.note = error
            return render.bedword(pageform)

        print(taskdir)

        utilities.gen_bedword_files(taskdir,
                                    email,
                                    filename,
                                    extension,
                                    audio_length,
                                    diarize,
                                    punctuate,
                                    output_formats,
                                    send_to_darla)

        if send_to_darla: # write darla files so it's nice and compatable
            utilities.gen_argfiles(taskdir,
                                    'bound',
                                    filename,
                                    audio_length, 
                                    email,
                                    delstopwords,
                                    maxbandwidth,
                                    delunstressedvowels)
            utilities.write_speaker_info(os.path.join(taskdir, 'speaker'), filename, sex)


        bedword_transcription.delay(taskdir, api_key)
        return render.success('')


if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
