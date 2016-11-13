#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import shutil
import codecs
import os
from web import form
import myform
import utilities
import allpipeline
import extract
import alignextract
from evaluate import run_evaluation
import asredit
import time
import srt_to_textgrid
import json
import base64
from mturk import mturk, mturksubmit
#google
from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials
# [END import_libraries]

render = web.template.render('templates/', base='layout')

urls = ('/', 'index', '/index', 'index', '/cite', 'cite', '/about', 'about', '/cave', 'cave', '/semi', 'semi', '/mturk', 'mturk', '/mturksubmit', 'mturksubmit', '/uploadsound', 'uploadsound', '/uploadtxttrans', 'uploadtxttrans', '/uploadboundtrans', 'uploadboundtrans', '/uploadtextgrid', 'uploadtextgrid', '/allpipeline', allpipeline.app_allpipeline, '/extract', extract.app_extract, '/alignextract', alignextract.app_alignextract, '/uploadeval', 'uploadeval', '/asredit', asredit.app_asredit, '/uploadyt', 'uploadyt', '/googlespeech', 'googlespeech', '/downloadsrttrans', 'downloadsrttrans')

app = web.application(urls, globals())
web.config.debug = True

MINDURATION = 30 # minimum uploaded audio duration in minutes

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

def make_uploadfile():
    return myform.MyFile('uploadfile',
                       post='Longer recordings (of at least {0} minutes) are recommended. Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.'.format(MINDURATION),
                       description='Upload a .wav or .mp3 file:')

def make_filelink():
    return form.Textbox('filelink',
                        form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                          post='Long, single-speaker videos with no music work best.',
                          description='or copy and paste a link to a YouTube video:')

def make_email():
    return form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address.'),
                         post='We will not store or distribute your address.',
                         description='Your e-mail address:')

def make_delstopwords():
    f = myform.MyRadio('delstopwords',
                                     [('Y', 'Yes ', 'Y'),
                                      ('N', 'No ', 'N')],
                                     description='Filter out stop-words? ')
    f.value = 'Y'  # default
    return f

def speaker_form(filename, taskname):
    input_list = []
    taskname = form.Hidden(name="taskname", value=taskname)
    speaker_name = form.Textbox('name', description='Speaker ID: ')
    sex = myform.MyRadio('sex', [('M','Male ', 'M'), ('F','Female ', 'F'), ('F','Child ', 'C')], description='Sex: ')
    sex.value = 'M'  # default if not checked

    filename = form.Hidden(value=filename, name='filename')

    speakers = myform.MyForm(taskname,
                            speaker_name,
                            sex,
                            filename)

    return speakers()


class uploadsound:
    uploadfile = make_uploadfile()
    filelink = make_filelink()
    delstopwords = make_delstopwords()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]

    datadir = utilities.read_filepaths()['DATA']
    
    def GET(self):
        uploadsound = myform.MyForm(self.uploadfile,
                                    self.filelink,
                                    self.delstopwords,
                                    self.email, self.taskname, self.submit)
        form = uploadsound()
        return render.speakerssound(form, "")

    def POST(self):
        uploadsound = myform.MyForm(self.uploadfile,
                                    self.filelink,
                                    self.delstopwords,
                                    self.email, self.taskname, self.submit,
                                    validators = self.soundvalid)
        form = uploadsound()
        x = web.input(uploadfile={})
        filenames = [] # for use in speaker form

        if not form.validates(): #not validated
            return render.speakerssound(form, "")

        else:
            #make taskname
            taskname, audiodir, error = utilities.make_task(self.datadir)
            if error!="":
                form.note = error
                return render.speakerssound(form, "")

            form.taskname.value = taskname

            # if youtube link filled
            if x.filelink!="":
                filename, error = utilities.youtube_wav(x.filelink, audiodir, taskname)
                if error!="":
                    form.note = error
                    return render.speakerssound(form, "")

                samprate, total_size, chunks, error = utilities.sox_conversion(filename,
                                                                              audiodir, dochunk=20)
                if error!="":
                    form.note = error
                    return render.speakerssound(form, "")

                filename = os.path.splitext(filename)[0]

                utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+'.chunks'))

            # else uploaded file
            elif 'uploadfile' in x:

                #sanitize filename
                filename, extension = utilities.get_basename(x.uploadfile.filename)

                if extension not in ['.wav', '.mp3']:
                    form.note = "Please upload a .wav or .mp3 audio file."
                    return render.speakerssound(form, "")

                else:
                    samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                                                                 filename,
                                                                                 extension,
                                                                                 x.uploadfile.file.read(),
                                                                                 dochunk=20)

                    if error!="":
                        form.note = error
                        return render.speakerssound(form, "")

                    utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+'.chunks'))

            if total_size < MINDURATION:
                form.note = "Warning: Your file totals only {:.2f} minutes of speech. We recommend at least {:.0f} minutes for best results.".format(total_size, MINDURATION)

            #generate argument files
            utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'asr', form.email.value, samprate, form.delstopwords.value)

            #show speaker form by adding fields to existing form and re-rendering
            speakers = speaker_form(filename, form.taskname.value)
            return render.speakerssound(form, speakers)

class googlespeech:
    datadir = utilities.read_filepaths()['DATA']
    # [START authenticating]
    DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                     'version={apiVersion}')
    uploadfile = make_uploadfile()
    delstopwords = make_delstopwords()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = [form.Validator('Please upload a sound file.',
                                 lambda x:x.uploadfile)]
    # Application default credentials provided by env variable
    # GOOGLE_APPLICATION_CREDENTIALS
    def get_speech_service(self):
        credentials = GoogleCredentials.get_application_default().create_scoped(
            ['https://www.googleapis.com/auth/cloud-platform'])
        http = httplib2.Http()
        credentials.authorize(http)

        return discovery.build(
            'speech', 'v1beta1', http=http, discoveryServiceUrl=self.DISCOVERY_URL)

    def GET(self):
        googlespeech = myform.MyForm(self.uploadfile,
                                     self.delstopwords,
                                     self.email,
                                     self.taskname,
                                     self.submit)
        form = googlespeech()
        return render.googlespeech(form)

    def POST(self):
        googlespeech = myform.MyForm(self.uploadfile,
                                     self.delstopwords,
                                     self.email,
                                     self.taskname,
                                     self.submit)
        form = googlespeech()
        x = web.input(uploadfile={})

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)
        if extension not in ['.wav', '.mp3']:
            form.note = "Please upload a .wav or .mp3 file."
            return render.speakersyt(form)
        else:
            with x.uploadfile.file as speech:
            # Base64 encode the binary audio file for inclusion in the JSON
            # request.
                # split into minute chunks
                taskname, audiodir, error = utilities.make_task(self.datadir)
                filename, extension = utilities.get_basename(x.uploadfile.filename)
                samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                                                                 filename,
                                                                                 extension,
                                                                                 x.uploadfile.file.read(),
                                                                                 dochunk=50)
                service = self.get_speech_service()
                total_msg = []

                # TODO: chunks are just the intervals. need to get the actual files
                for ci, chunk in enumerate(chunks):
                    # get the file and read it in

                    chunk_file = open(os.path.join(audiodir,'splits',filename+'.split{0:03d}.wav'.format(ci+1)))
                    speech_content = base64.b64encode(chunk_file.read())
                    service_request = service.speech().syncrecognize(
                    body={
                        'config': {
                            # There are a bunch of config options you can specify. See
                            # https://goo.gl/KPZn97 for the full list.
                            'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                            'sampleRate': 16000,  # 16 khz
                            # See https://goo.gl/A9KJ1A for a list of supported languages.
                            'languageCode': 'en-US',  # a BCP-47 language tag
                        },
                        'audio': {
                            'content': speech_content.decode('UTF-8')
                            }
                        })
                    response = service_request.execute()
                    sentences = "".join(map(lambda x: x['alternatives'][0]['transcript'], response['results']))
                    total_msg.append(sentences)


                return render.success(" ".join(total_msg))



                # speech_content = base64.b64encode(speech.read())


                # # [END construct_request]
                # # [START send_request]
                # response = service_request.execute()
                # print(json.dumps(response))
                # return render.success(json.dumps(response))

class uploadyt:
    uploadfile = make_uploadfile()
    email = make_email()
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = [form.Validator('Please upload a sound file.',
                                 lambda x:x.uploadfile)]

    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
        uploadyt = myform.MyForm(self.uploadfile,
                                 self.email,
                                 self.taskname,
                                 self.submit)
        form = uploadyt()
        return render.speakersyt(form)

    def POST(self):
        uploadyt = myform.MyForm(self.uploadfile,
                                 self.email,
                                 self.taskname,
                                 self.submit)
        form = uploadyt()
        x = web.input(uploadfile={})

        if not form.validates(): #not validated
            return render.speakersyt(form)

        #create new task
        taskname, audiodir, error = utilities.make_task(self.datadir)
        if error!="":
            form.note = error
            return render.speakersyt(form)

        form.taskname.value = taskname

        #sanitize filename
        filename, extension = utilities.get_basename(x.uploadfile.filename)
        if extension not in ['.wav', '.mp3']:
            form.note = "Please upload a .wav or .mp3 file."
            return render.speakersyt(form)
        else:

            error = utilities.convert_to_video(audiodir, filename, extension, x.uploadfile.file.read())
            if error:
                form.note = error
                return render.speakersyt(form)

            videofile = os.path.join(audiodir, filename+'.mp4')
            video_id, error = utilities.upload_youtube(form.taskname.value, videofile)

            o = open(os.path.join(audiodir, 'video_id.txt'), 'w')
            o.write(video_id)
            o.close()

            if error:
                form.note = error
                return render.speakersyt(form)

            error = utilities.send_ytupload_email(video_id, form.taskname.value, form.email.value, filename)
            if error:
                form.note = error
                return render.speakersyt(form)

            return render.success("Successfully uploaded! Please check your e-mail and re-visit the site in a few hours.")

class downloadsrttrans:
    taskname = form.Textbox('taskname',
                            form.notnull,
                            description='The taskname ID sent to your e-mail')
    delstopwords = make_delstopwords()
    email = make_email()

    submit = form.Button('submit', type='submit', description='Submit')
    soundvalid = [form.Validator('Please enter a taskname and video ID to continue with your job',
                  lambda x: (x.taskname!='' and x.video_id!=''))]

    datadir = utilities.read_filepaths()['DATA']

    def GET(self):
        downloadsrttrans = myform.MyForm(self.taskname,
                                         self.delstopwords,
                                        self.email,
                                        self.submit)
        form = downloadsrttrans()
        return render.speakerssrttrans(form, "")

    def POST(self):
        downloadsrttrans = myform.MyForm(self.taskname,
                                         self.delstopwords,
                                        self.email,
                                        self.submit)
        form = downloadsrttrans()

        if not form.validates(): #not validated
            return render.speakerssrttrans(form, "")

        taskname = form.taskname.value

        audiodir = os.path.join(self.datadir, taskname+'.audio')

        srtfile = os.path.join(audiodir, 'ytresults.en.srt')

        if not os.path.exists(srtfile):
            #try to download it
            video_id = open(os.path.join(audiodir, 'video_id.txt')).read().strip()
            error = utilities.download_youtube(audiodir, 'ytresults', video_id)
            if error:
                form.note = error
                return render.speakerssrttrans(form, "")

        srt_to_textgrid.convert(srtfile)

        filename = [filename for filename in os.listdir(audiodir) if not filename.startswith('converted') and (filename.endswith('wav') or filename.endswith('mp3'))][0]   #name of audio file (TODO: this is hacky)

        filename, extension = os.path.splitext(filename)

        # now run same code as uploadboundtrans (TODO later: abstract away)
        chunks, error = utilities.write_sentgrid_as_lab(self.datadir, taskname, filename, os.path.join(audiodir, 'ytresults.en.TextGrid'), 'cmudict.forhtk.txt')
        if error!="":
            form.note = error
            return render.speakerssrttrans(form, "")

        samprate, filesize, chunks, error = utilities.process_audio(audiodir, filename, extension, None, chunks)
        if error!="":
            form.note = error
            return render.speakerssrttrans(form, "")

        filenames = [(filename, filename)]

        utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+'.chunks'))
        utilities.gen_argfiles(self.datadir, taskname, filename, 'boundalign', form.email.value, samprate, form.delstopwords.value)

        speakers = speaker_form(filename, taskname)

        return render.speakerssrttrans(form, speakers)

class uploadtxttrans:
    uploadfile = make_uploadfile()
    uploadtxtfile = myform.MyFile('uploadtxtfile',
                                    form.notnull,
                                    post='We recommend creating this file using Notepad or TextEdit (with <a href="http://scttdvd.com/post/65242711516/how-to-get-rid-of-smart-quotes-osx-mavericks" target="_blank">smart replace turned off</a>) or emacs or any other plaintext editor. Transcripts created by "rich text" editors like Word may contain markup that will interfere with your results.',
                                  description='Manual transcription as a .txt file:')
    filelink = make_filelink()
    delstopwords = make_delstopwords()
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
                                    self.email, self.taskname, self.submit)
        form = uploadtxttrans()
        return render.speakerstxttrans(form, "")

    def POST(self):
        uploadtxttrans = myform.MyForm(self.uploadfile,
                                 self.filelink,
                                 self.uploadtxtfile,
                                 self.delstopwords,
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

        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'txtalign', form.email.value, samprate, form.delstopwords.value)

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
                                    self.email, self.taskname, self.submit)
        form = uploadboundtrans()
        return render.speakersboundtrans(form, "")

    def POST(self):
        uploadboundtrans = myform.MyForm(self.uploadfile,
                                 self.filelink,
                                 self.uploadboundfile,
                                 self.delstopwords,
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
        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'boundalign', form.email.value, samprate, form.delstopwords.value)

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
                                       self.email, self.taskname, self.submit,
                                       validators = self.soundvalid)
        form = uploadtextgrid()
        return render.speakerstextgrid(form, "")

    def POST(self):
        uploadtextgrid = myform.MyForm(self.uploadfile,
                                 self.filelink,
                                 self.uploadTGfile,
                                 self.delstopwords,
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

        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'extract', form.email.value, delstopwords=form.delstopwords.value)

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

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
