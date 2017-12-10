#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request
from wtforms import Form, HiddenField

import shutil
import codecs
import os
import utilities
#import allpipeline
#import extract
#import alignextract
from evaluate import run_evaluation
#import asredit
import time
import srt_to_textgrid
import json
import sys

from formfields import make_uploadfile, make_email, make_speaker, make_filteropts, validate_upload, process_audio_upload
from allpipeline import allpipeline

MINDURATION = 2 # minimum uploaded audio duration in minutes
app = Flask(__name__)

urls = ('/', 'index',
        '/index', 'index',
        '/cite', 'cite',
        '/about', 'about',
        '/cave', 'cave',
        '/semi', 'semi',
        '/mturk', 'mturk',
        '/stopwords', 'stopwords',
        '/mturksubmit', 'mturksubmit',
        '/uploadsound', 'uploadsound',
        '/uploadtxttrans', 'uploadtxttrans',
        '/uploadboundtrans', 'uploadboundtrans',
        '/uploadtextgrid', 'uploadtextgrid',
#        '/allpipeline', allpipeline.app_allpipeline,
#        '/extract', extract.app_extract,
#        '/alignextract', alignextract.app_alignextract,
        '/uploadeval', 'uploadeval',
#        '/asredit', asredit.app_asredit,
        '/uploadyt', 'uploadyt',
        '/googlespeech', 'googlespeech',
        '/downloadsrttrans', 'downloadsrttrans')

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/cite', methods=['GET'])
def cite():
    return render_template('cite.html')

@app.route('/cave', methods=['GET'])
def cave():
    return render_template('cave.html')

@app.route('/semi', methods=['GET'])
def semi():
    return render_template('semi.html')

@app.route('/stopwords', methods=['GET'])
def stopwords():
    return render_template('stopwords.html', wordlist = ' '.join(open('stopwords.txt').read().split()))

class UploadSound(Form):
    taskname = HiddenField('taskname')
    audio = make_uploadfile()
    email = make_email()
    speaker_name, speaker_sex = make_speaker()
    delstopwords, delunstressedvowels, filterbandwidths = make_filteropts()

@app.route('/cavejob', methods=['GET', 'POST'])
def cavejob():
    form = UploadSound(request.form)
    if request.method == 'POST' and form.validate():
        f = request.files['audio']
        if not validate_upload(f, form.audio, ['wav', 'mp3']):
            return render_template('caveform.html', form=form)
        taskname, filename, samprate, chunks, error = process_audio_upload(f, app.config['DATA'])
        if error!='':
            form.audio.errors.append(error)
            return render_template('caveform.html', form=form)
        form.taskname.value = taskname
        utilities.write_chunks(chunks, os.path.join(app.config['DATA'], taskname+'.chunks'))
        #generate argument files
        utilities.gen_argfiles(app.config['DATA'],
                               taskname,
                               filename,
                               'asr',
                               request.form['email'],
                               samprate,
                               request.form['delstopwords'],
                               request.form['filterbandwidths'],
                               request.form['delunstressedvowels'])
        return allpipeline(app.config['DATA'],
                    taskname,
                    filename,
                    request.form['speaker_name'],
                    request.form['speaker_sex'],
                    app.config['PASSWORD'],
                    app.config['URLBASE'])
    return render_template('caveform.html', form=form)

    """




            #show speaker form by adding fields to existing form and re-rendering
            speakers = speaker_form(filename, form.taskname.value)
            return render.speakerssound(form, speakers)
        """
"""
class googlespeech:
    speaker_name = form.Textbox('name', description='Speaker ID: ')
    sex = myform.MyRadio('sex', [('M','Male ', 'M'), ('F','Female ', 'F'), ('F','Child ', 'C')], description='Speaker Sex: ')
    sex.value = 'M'  # default if not checked
    filepaths = utilities.read_filepaths()
    appdir = '.'
    datadir = filepaths['DATA']

    uploadfile = make_uploadfile()
    delstopwords = make_delstopwords()
    delunstressedvowels = make_delunstressedvowels()
    filterbandwidths = make_filterbandwidths()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = [form.Validator('Please upload a sound file.',
                                 lambda x:x.uploadfile)]

    def GET(self):

        googlespeech = myform.MyForm(self.uploadfile,
                                     self.delstopwords,
                                     self.delunstressedvowels,
                                     self.filterbandwidths,
                                     self.email,
                                     self.taskname,
                                     self.speaker_name,
                                     self.sex,
                                     self.submit)
        form = googlespeech()
        return render.googlespeech(form)

    def POST(self):
        googlespeech = myform.MyForm(self.uploadfile,
                                     self.delstopwords,
                                     self.delunstressedvowels,
                                     self.filterbandwidths,
                                     self.email,
                                     self.taskname,
                                     self.sex,
                                     self.speaker_name,
                                     self.submit)
        form = googlespeech()
        x = web.input(uploadfile={})

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)
        if extension not in ['.wav', '.mp3']:
            form.note = "Please upload a .wav or .mp3 file."
            return render.speakersyt(form)
        else:
            gstorage = get_storage_service(self.filepaths['GOOGLESPEECH'])
            service = get_speech_service(self.filepaths['GOOGLESPEECH'])
            taskname, audiodir, error = utilities.make_task(self.datadir)
            filename, extension = utilities.get_basename(x.uploadfile.filename)

            utilities.write_speaker_info(os.path.join(self.datadir, taskname+'.speaker'), x.name, x.sex)

            utilities.send_init_email('googleasr', x.email, filename)
            if celeryon:
                # upload entire file onto google cloud storage
                samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                                                  filename,
                                                                  extension,
                                                                  x.uploadfile.file.read(),
                                                                  dochunk=None)
                result = gcloudupload.delay(gstorage,
                                            audiodir,
                                            filename,
                                            taskname,
                                            x.email)
                while not result.ready():
                    pass

                # uncomment to test throttle by sending 4 speech reqs
                # for i in range(4):
                result = asyncrec.delay(service,
                                       self.datadir,
                                       taskname,
                                       audiodir,
                                       filename,
                                       samprate,
                                       x.email)
                while not result.ready():
                    pass

            else:
                # create chunked files
                samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                                                  filename,
                                                                  extension,
                                                                  x.uploadfile.file.read(),
                                                                  dochunk=50)
                syncrec(service,
                        self.datadir,
                        taskname,
                        audiodir,
                        filename,
                        chunks,
                        samprate)
            #TODO: why do we need datadir, audiodir, etc? Reduce redundancy in these filenames

            utilities.gen_argfiles(self.datadir, taskname, filename, 'googleasr', x.email, samprate, x.delstopwords, x.filterbandwidths, x.delunstressedvowels)

            if celeryon:
                result = align_extract.delay(os.path.join(self.datadir, taskname), self.appdir)
                while not result.ready():
                    pass
            else:
                align_extract(os.path.join(self.datadir, taskname),self.appdir)

            return render.success("You may now close this window. We will email you the results.")



class uploadtxttrans:
    uploadfile = make_uploadfile()
    uploadtxtfile = myform.MyFile('uploadtxtfile',
                                    form.notnull,
                                    post='We recommend creating this file using Notepad or TextEdit (with <a href="http://scttdvd.com/post/65242711516/how-to-get-rid-of-smart-quotes-osx-mavericks" target="_blank">smart replace turned off</a>) or emacs or any other plaintext editor. Transcripts created by "rich text" editors like Word may contain markup that will interfere with your results.',
                                  description='Manual transcription as a .txt file:')
    filelink = make_filelink()
    delstopwords = make_delstopwords()
    delunstressedvowels = make_delunstressedvowels()
    filterbandwidths = make_filterbandwidths()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]

    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
        uploadtxttrans = myform.MyForm(self.uploadfile,
                                       self.filelink,
                                       self.uploadtxtfile,
                                       self.delstopwords,
                                       self.delunstressedvowels,
                                       self.filterbandwidths,
                                       self.email, self.taskname, self.submit)
        form = uploadtxttrans()
        return render.speakerstxttrans(form, "")

    def POST(self):
        uploadtxttrans = myform.MyForm(self.uploadfile,
                                       self.filelink,
                                       self.uploadtxtfile,
                                       self.delstopwords,
                                       self.delunstressedvowels,
                                       self.filterbandwidths,
                                       self.email, self.taskname, self.submit,
                                       validators = self.soundvalid)
        form = uploadtxttrans()
        x = web.input(uploadfile={}, uploadtxtfile={})

        if not form.validates(): #not validated
            return render.speakerstxttrans(form, "")

        filenames = []
        txtfilename, txtextension = utilities.get_basename(x.uploadtxtfile.filename)

        if txtextension != '.txt':  #TODO: check plaintext validity
            form.note = 'Upload a transcript with a .txt extension.'
            return render.speakerstxttrans(form, "")

        #create new task
        taskname, audiodir, error = utilities.make_task(self.datadir)
        if error!="":
            form.note = error
            return render.speakerstxttrans(form, "")

        form.taskname.value = taskname

        if 'uploadfile' in x:
            #sanitize filename
            filename, extension = utilities.get_basename(x.uploadfile.filename)
            if extension not in ['.wav', '.mp3']:
                form.note = "Please upload a .wav or .mp3 file."
                return render.speakerstxttrans(form, "")
            else:
                error = utilities.write_hyp(self.datadir, form.taskname.value, filename, x.uploadtxtfile.file.read(), 'cmudict.forhtk.txt')
                if error!="":
                    form.note = error
                    return render.speakerstxttrans(form, "")

                samprate, total_size, _, error = utilities.process_audio(audiodir,
                                             filename, extension,
                    x.uploadfile.file.read(),
                dochunk=None)
                if error!="":
                    form.note = error
                    return render.speakerstxttrans(form, "")
                filenames = [(filename, filename)]

        elif x.filelink!='':

            filename = utilities.youtube_wav(x.filelink, audiodir, taskname)
            error = utilities.write_hyp(self.datadir, form.taskname.value, filename, x.uploadtxtfile.file.read(), 'cmudict.forhtk.txt')
            if error!="":
                form.note = error
                return render.speakerttxttrans(form, "")
            samprate, total_size, chunks, error = utilities.sox_conversion(filename, audiodir, dochunk=None)
            if error!="":
                form.note = error
                return render.speakerstxttrans(form, "")

            filenames = [(filename, x.filelink)]

        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'txtalign', form.email.value, samprate, form.delstopwords.value, form.filterbandwidths.value, form.delunstressedvowels.value)

        speakers = speaker_form(filename, taskname)

        return render.speakerstxttrans(form, speakers)

class uploadboundtrans:
    uploadfile = make_uploadfile()
    filelink = make_filelink()
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

    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]

    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
        uploadboundtrans = myform.MyForm(self.uploadfile,
                                         self.filelink,
                                         self.uploadboundfile,
                                         self.delstopwords,
                                         self.delunstressedvowels,
                                         self.filterbandwidths,
                                         self.email, self.taskname, self.submit)
        form = uploadboundtrans()
        return render.speakersboundtrans(form, "")

    def POST(self):
        uploadboundtrans = myform.MyForm(self.uploadfile,
                                         self.filelink,
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

        filenames = []
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

        if 'uploadfile' in x:
            #sanitize filename
            filename, extension = utilities.get_basename(x.uploadfile.filename)

            if extension not in ['.wav', '.mp3']:
                form.note = "Please upload a .wav or .mp3 file."
                return render.speakersboundtrans(form, "")
            else:
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

                filenames = [(filename, filename)]

        elif x.filelink!='':

            filename = utilities.youtube_wav(x.filelink, audiodir, taskname)

            chunks, error = utilities.write_sentgrid_as_lab(self.datadir, form.taskname.value, filename, boundfilename+boundextension, 'cmudict.forhtk.txt')
            if error!="":
                form.note = error
                return render.speakersboundtrans(form, "")

            samprate, total_size, chunks, error = utilities.sox_conversion(filename, audiodir, dochunk=chunks)
            if error!="":
                form.note = error
                return render.speakersboundtrans(form, "")

            filenames = [(filename, x.filelink)]

        utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+'.chunks'))
        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'boundalign', form.email.value, samprate, form.delstopwords.value, form.filterbandwidths.value, form.delunstressedvowels.value)

        speakers = speaker_form(filename, taskname)

        return render.speakersboundtrans(form, speakers)

class uploadtextgrid:
    uploadfile = make_uploadfile()
    filelink = make_filelink()
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

    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]

    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
        uploadtextgrid = myform.MyForm(self.uploadfile,
                                       self.filelink,
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
                                       self.filelink,
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

        filenames = []
        tgfilename, tgextension = utilities.get_basename(x.uploadTGfile.filename)

        if tgextension != '.textgrid':
            form.note = 'Upload a file with a .TextGrid extension.'
            return render.speakerstextgrid(form, "")

        if 'uploadfile' in x:
            #sanitize filename
            filename, extension = utilities.get_basename(x.uploadfile.filename)

            if extension not in ['.wav', '.mp3']:
                form.note = "Please upload a .wav or .mp3 file."
                return render.speakerstextgrid(form, "")

            else:
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

                filenames.append((filename, filename))

        elif x.filelink!='':

            #make taskname
            taskname, audiodir, error = utilities.make_task(self.datadir)
            if error!="":
                    form.note = error
                    return render.speakerstextgrid(form, "")

            form.taskname.value = taskname

            filename = utilities.youtube_wav(x.filelink, audiodir, taskname)
            samprate, total_size, chunks, error = utilities.sox_conversion(filename, audiodir, dochunk=None)
            if error!="":
                form.note = error
                return render.speakerstextgrid(form, "")

            filenames = [(filename, x.filelink)]

        utilities.write_textgrid(self.datadir, form.taskname.value, filename, utilities.read_textupload(x.uploadTGfile.file.read()))

        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'extract', form.email.value, delstopwords=form.delstopwords.value, maxbandwidth=form.filterbandwidths.value, delunstressedvowels=form.delunstressedvowels.value)

        speakers = speaker_form(filename, taskname)

        return render.speakerstextgrid(form, speakers)

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
"""
if __name__=="__main__":
    app.secret_key = 'flaskonfire'
    filepaths = utilities.read_filepaths()
    app.config['DATA'] = filepaths['DATA']
    app.config['PASSWORD'] = filepaths['PASSWORD']
    app.config['URLBASE'] = filepaths['URLBASE']
    app.run(debug=True)
