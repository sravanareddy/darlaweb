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

render = web.template.render('templates/', base='layout')

urls = ('/', 'index', '/index', 'index', '/cite', 'cite', '/about', 'about', '/cave', 'cave', '/semi', 'semi', '/uploadsound', 'uploadsound', '/uploadtxttrans', 'uploadtxttrans', '/uploadboundtrans', 'uploadboundtrans', '/uploadtextgrid', 'uploadtextgrid', '/allpipeline', allpipeline.app_allpipeline, '/extract', extract.app_extract, '/alignextract', alignextract.app_alignextract, '/uploadeval', 'uploadeval', '/asredit', asredit.app_asredit, '/uploadyt', 'uploadyt', '/downloadsrttrans', 'downloadsrttrans')

app = web.application(urls, globals())
web.config.debug = True
        
class index:
    def GET(self):
        return render.index()

class cite:
    def GET(self):
        return render.cite()

class about:
    def GET(self):
        return render.about()

class cave:
    def GET(self):
        return render.cave()

class semi:
    def GET(self):
        return render.semi()

def speaker_form(completed_form, filename, taskname): #send in the completed form too
  input_list = []
  taskname = form.Hidden(name="taskname", value=taskname)
  speaker_name = form.Textbox('name', form.notnull, description='Speaker ID: ')
  sex = myform.MyRadio('sex', [('M','Male ', 'M'), ('F','Female ', 'F'), ('F','Child ', 'C')], description='Sex: ')
  filename = form.Hidden(value=filename, name='filename')
  speakers = myform.MyForm(taskname,
                           speaker_name,
                           sex,
                           filename)
  return render.speakerssound(completed_form, speakers())
    
class uploadsound:
    MINDURATION = 30 #in minutes
    uploadfile = myform.MyFile('uploadfile',
                           post='Longer recordings (of at least {0} minutes) are recommended. Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.'.format(MINDURATION),
                           description='Upload a .wav or .mp3 file:')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                              post='Long, single-speaker videos with no music work best.',
                              description='or copy and paste a link to a YouTube video:')
    dialect = form.Radio('dialect',
                         [('standard', 'Standard American '),
                          ('southern', 'Southern ')],
                         value = 'standard',
                         post='Selecting the closest appropriate dialect for the acoustic model may increase transcription accuracy. Other dialects may be added in the future.',
                         description='Dialect of the speaker:')
    lw = form.Radio('lw',
                    [('7', 'Free speech or reading passage '),
                     ('3', 'Word list ')],
                    value = '7',
                    post='If your recording contains both styles, select the free speech option.',
                    description='Speech Type',)
    email = form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address.'),
                         post='We will not store or distribute your address.',
                         description='Your e-mail address:')
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')
    
    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]
    
    datadir = open('filepaths.txt').readline().split()[1]
      
    def GET(self):
        self.dialect.value = 'standard'
        self.lw.value = '7' #defaults
        uploadsound = myform.MyForm(self.uploadfile, 
                                    self.filelink, 
                                    self.dialect, 
                                    self.lw, self.email, self.taskname, self.submit)
        form = uploadsound()
        return render.speakerssound(form, "")

    def POST(self):
        uploadsound = myform.MyForm(self.uploadfile, 
                                    self.filelink, 
                                    self.dialect, 
                                    self.lw, self.email, self.taskname, self.submit,
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
            
            if x.filelink!="": 
                filename, error = utilities.youtube_wav(x.filelink, audiodir, taskname)
                if error!="":
                    form.note = error
                    return render.speakerssound(form, "")
        
                samprate, total_size, chunks, error = utilities.soxConversion(filename,
                                                                              audiodir, dochunk=20)
                if error!="":
                    form.note = error
                    return render.speakerssound(form, "")

                filename = os.path.splitext(filename)[0]
                
                utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+filename+'.chunks'))
                
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
                    
                    utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+filename+'.chunks'))
                
            if total_size < self.MINDURATION:  
                form.note = "Warning: Your file totals only {:.2f} minutes of speech. We recommend at least {:.0f} minutes for best results.".format(total_size, self.MINDURATION)
                    
            #generate argument files
            utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'asr', form.email.value, samprate, form.lw.value, form.dialect.value)
                    
            #show speaker form by adding fields to existing form and re-rendering
            return speaker_form(form, filename, taskname)

class uploadyt:
    
    uploadfile = myform.MyFile('uploadfile',
                               post='Your uploaded file is stored temporarily on the Dartmouth servers in order to process your job, and deleted after.',
                               description='Your .wav or .mp3 file:')
    email = form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address'),
                                     post='We will not store or distribute your address.',
                                     description='Your e-mail address:')
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')
    soundvalid = [form.Validator('Please upload a sound file.',
                                 lambda x:x.uploadfile)]

    datadir = open('filepaths.txt').readline().split()[1]

    def GET(self):
        uploadyt = myform.MyForm(self.uploadfile, self.email, self.taskname, self.submit)
        form = uploadyt()
        return render.speakersyt(form, "")

    def POST(self):
        uploadyt = myform.MyForm(self.uploadfile, self.email, self.taskname, self.submit)
        form = uploadyt()
        x = web.input(uploadfile={})

        if not form.validates(): #not validated
            return render.speakersyt(form, "")

        #create new task                                                                                 
        taskname, audiodir, error = utilities.make_task(self.datadir)
        if error!="":
            form.note = error
            return render.speakersyt(form, "")

        form.taskname.value = taskname

        #sanitize filename                                                                        
        filename, extension = utilities.get_basename(x.uploadfile.filename)
        if extension not in ['.wav', '.mp3']:
            form.note = "Please upload a .wav or .mp3 file."
            return render.speakersyt(form, "")
        else:
            
            error = utilities.convert_to_video(audiodir, filename, extension, x.uploadfile.file.read())
            if error:
                form.note = error
                return render.speakersyt(form, "")

            videofile = os.path.join(audiodir, filename+'.mp4')
            video_id, error = utilities.upload_youtube(form.taskname.value, videofile)
            
            if error:
                form.note = error
                return render.speakersyt(form, "")

            error = utilities.send_ytupload_email(video_id, form.taskname.value, form.email.value, filename)
            if error:
                form.note = error
                return render.speakersyt(form, "")
            
            return 'Successfully uploaded! Please check your e-mail.'

class downloadsrttrans:
    taskname = form.Textbox('taskname',
                            form.notnull,
                            description='The taskname ID sent to your e-mail')
    video_id = form.Textbox('video_id',
                            form.notnull,
                            description='The video ID sent to your e-mail')
    email = form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address'),
                                     post='We will not store or distribute your address.',
                                     description='Your e-mail address:')
    
    submit = form.Button('submit', type='submit', description='Submit')
    soundvalid = [form.Validator('Please enter a taskname and video ID to continue with your job',
                  lambda x: (x.taskname!='' and x.video_id!=''))]

    datadir = open('filepaths.txt').readline().split()[1]

    def speaker_form(self, completed_form, filenames): #send in the completed form too                
        input_list = []
        taskname = form.Hidden(name="taskname",value=completed_form.taskname.value)
        numfiles = form.Hidden(name="numfiles",value=len(filenames))
        input_list.extend([taskname,numfiles])
        #TODO: no need to generalize to multiple speakers                                                       
        filename = form.Hidden(value=filenames[0][0],name='filename0')
        speaker_name = form.Textbox('name0',
                         form.notnull,
                         pre="File Name: "+filenames[0][1],
                         description='Speaker ID')
        sex = myform.MyRadio('sex0',
                        [('M','Male', 'M0'),('F','Female', 'F0'),('F','Child', 'C0')],
                        description='Sex'
                        )
        input_list.extend([speaker_name,sex,filename])
        speakers = myform.ListToForm(input_list)
        s = speakers()
        return render.speakerssrttrans(completed_form, s)
    
    def GET(self):
        downloadsrttrans = myform.MyForm(self.taskname,
                                        self.video_id,
                                        self.email,
                                        self.submit)
        form = downloadsrttrans()
        return render.speakerssrttrans(form, "")

    def POST(self):
        downloadsrttrans = myform.MyForm(self.taskname,
                                        self.video_id,
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
            error = utilities.download_youtube(audiodir, 'ytresults', form.video_id.value)
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

        samprate, filesize, chunks, error = utilities.soxConversion(filename+extension, audiodir, dochunk=chunks)
        if error!="":
            form.note = error
            return render.speakerssrttrans(form, "")

        filenames = [(filename, filename)]

        utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+filename+'.chunks'))
        utilities.gen_argfiles(self.datadir, taskname, filename, 'boundalign', form.email.value, samprate)
        return self.speaker_form(form, filenames)

class uploadtxttrans:
    uploadfile = myform.MyFile('uploadfile',
                               post='Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.',
                               description='Your .wav or .mp3 file:')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                            post='',
                            description='or copy and paste a link to a YouTube video:')
    uploadtxtfile = myform.MyFile('uploadtxtfile',
                                    form.notnull,
                                    post='We recommend creating this file using Notepad or TextEdit (with <a href="http://scttdvd.com/post/65242711516/how-to-get-rid-of-smart-quotes-osx-mavericks" target="_blank">smart replace turned off</a>) or emacs or any other plaintext editor. Transcripts created by "rich text" editors like Word may contain markup that will interfere with your results.',
                                  description='Manual transcription as a .txt file:')
    email = form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address'),
                                     post='We will not store or distribute your address.',
                                     description='Your e-mail address:')
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')
    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]

    datadir = open('filepaths.txt').readline().split()[1]

    def speaker_form(self, completed_form, filenames, taskname): #send in the completed form too           
        input_list = []
        taskname = form.Hidden(name="taskname",value=taskname)
        numfiles = form.Hidden(name="numfiles",value=len(filenames))
        input_list.extend([taskname, numfiles])
        #TODO: no need to generalize to multiple speakers                                                  
        filename = form.Hidden(value=filenames[0][0],name='filename0')
        speaker_name = form.Textbox('name0',
                         form.notnull,
                         pre="File Name: "+filenames[0][1],
                         description='Speaker ID')
        sex = myform.MyRadio('sex0',
                        [('M','Male', 'M0'),('F','Female', 'F0'),('F','Child', 'C0')],
                        description='Sex'
                        )
        input_list.extend([speaker_name,sex,filename])
        speakers = myform.ListToForm(input_list)
        s = speakers()
        return render.speakerstxttrans(completed_form, s)

    def GET(self):
        uploadtxttrans = myform.MyForm(self.uploadfile,
                                    self.filelink,
                                    self.uploadtxtfile,
                                    self.email, self.taskname, self.submit)
        form = uploadtxttrans()
        return render.speakerstxttrans(form, "")

    def POST(self):
        uploadtxttrans = myform.MyForm(self.uploadfile,
                                 self.filelink,
                                 self.uploadtxtfile,
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
            samprate, total_size, chunks, error = utilities.soxConversion(filename, audiodir, dochunk=None)
            if error!="":
                form.note = error
                return render.speakerstxttrans(form, "")

            filenames = [(filename, x.filelink)]

        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'txtalign', form.email.value, samprate)

        return self.speaker_form(form, filenames, taskname)

class uploadboundtrans:
    uploadfile = myform.MyFile('uploadfile',
                           post='Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.',
                           description='Your .wav or .mp3 file:')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                              post='',
                              description='or copy and paste a link to a YouTube video:')
    uploadboundfile = myform.MyFile('uploadboundfile',
                                 form.notnull,
                           post = 'Textgrid should contain a tier named "sentence" with sentence/breath group intervals.',
                           description='Manual transcription as a .TextGrid file:')
    email = form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address'),
                                     post='We will not store or distribute your address.',
                                     description='Your e-mail address:')
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]

    datadir = open('filepaths.txt').readline().split()[1]
    
    def speaker_form(self, completed_form, filenames, taskname): #send in the completed form too           
        input_list = []
        taskname = form.Hidden(name="taskname",value=taskname)
        numfiles = form.Hidden(name="numfiles",value=len(filenames))
        input_list.extend([taskname, numfiles])
        #TODO: no need to generalize to multiple speakers                                                  
        filename = form.Hidden(value=filenames[0][0],name='filename0')
        speaker_name = form.Textbox('name0',
                         form.notnull,
                         pre="File Name: "+filenames[0][1],
                         description='Speaker ID')
        sex = myform.MyRadio('sex0',
                        [('M','Male', 'M0'),('F','Female', 'F0'),('F','Child', 'C0')],
                        description='Sex'
                        )
        input_list.extend([speaker_name,sex,filename])
        speakers = myform.ListToForm(input_list)
        s = speakers()
        return render.speakersboundtrans(completed_form, s)
    
    def GET(self):
        uploadboundtrans = myform.MyForm(self.uploadfile,
                                    self.filelink, 
                                    self.uploadboundfile,  
                                    self.email, self.taskname, self.submit)
        form = uploadboundtrans()
        return render.speakersboundtrans(form, "")

    def POST(self):
        uploadboundtrans = myform.MyForm(self.uploadfile,
                                 self.filelink, 
                                 self.uploadboundfile,  
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
            
            samprate, total_size, chunks, error = utilities.soxConversion(filename, audiodir, dochunk=chunks)
            if error!="":
                form.note = error
                return render.speakersboundtrans(form, "")
            
            filenames = [(filename, x.filelink)]
          
        utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+filename+'.chunks'))
        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'boundalign', form.email.value, samprate)
        
        return self.speaker_form(form, filenames, taskname)

class uploadtextgrid:
    uploadfile = myform.MyFile('uploadfile',
                           post='Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.',
                           description='Your .wav or .mp3 file:')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                              post='',
                              description='or copy and paste a link to a YouTube video:')
    uploadTGfile = myform.MyFile('uploadTGfile',
                                 form.notnull,
                           post = '',
                           description='Corrected .TextGrid file')
    email = form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address'),
                                     post='We will not store or distribute your address.',
                                     description='Your e-mail address:')
    taskname = form.Hidden('taskname')
    submit = form.Button('submit', type='submit', description='Submit')

    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]
    
    datadir = open('filepaths.txt').readline().split()[1]    
    
    def speaker_form(self, completed_form, filenames, taskname): #send in the completed form too   
        input_list = []
        taskname = form.Hidden(name="taskname",value=taskname)
        numfiles = form.Hidden(name="numfiles",value=len(filenames))
        input_list.extend([taskname, numfiles])

        #TODO: no need to generalize to multiple speakers                                          
        filename = form.Hidden(value=filenames[0][0],name='filename0')
        speaker_name = form.Textbox('name0',
                                    form.notnull,
                                    pre="File Name: "+filenames[0][1],
                                    description='Speaker ID')
        sex = myform.MyRadio('sex0',
                             [('M','Male', 'M0'),('F','Female', 'F0'),('F','Child', 'C0')],
                             description='Sex'
                             )

        input_list.extend([speaker_name,sex,filename])

        speakers = myform.ListToForm(input_list)
        s = speakers()

        return render.speakerstextgrid(completed_form, s)
    
    def GET(self):
        uploadtextgrid = myform.MyForm(self.uploadfile,
                                    self.filelink, 
                                    self.uploadTGfile,  
                                       self.email, self.taskname, self.submit,
                                       validators = self.soundvalid)
        form = uploadtextgrid()
        return render.speakerstextgrid(form, "")

    def POST(self):
        uploadtextgrid = myform.MyForm(self.uploadfile,
                                 self.filelink, 
                                 self.uploadTGfile,  
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
            samprate, total_size, chunks, error = utilities.soxConversion(filename, audiodir, dochunk=None)
            if error!="":
                form.note = error
                return render.speakerstextgrid(form, "")
            
            filenames = [(filename, x.filelink)]
        
        utilities.write_textgrid(self.datadir, form.taskname.value, filename, utilities.read_textupload(x.uploadTGfile.file.read())) 

        utilities.gen_argfiles(self.datadir, form.taskname.value, filename, 'extract', form.email.value)
        
        return self.speaker_form(form, filenames, taskname)

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
    datadir = open('filepaths.txt').readline().split()[1]

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
