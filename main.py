#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import shutil
import codecs
import os
from web import form
import myform
import utilities
import zipfile
import tarfile
import allpipeline
import extract
import alignextract
from evaluate import run_evaluation

render = web.template.render('templates/', base='layout')

urls = ('/', 'index', '/uploadsound', 'uploadsound', '/uploadtrans', 'uploadtrans', '/uploadtextgrid', 'uploadtextgrid', '/allpipeline', allpipeline.app_allpipeline, '/extract', extract.app_extract, '/alignextract', alignextract.app_alignextract, '/uploadeval', 'uploadeval')

app = web.application(urls, globals())
web.config.debug = True
        
class index:
    def GET(self):
        return render.index()

class uploadsound:
    MINDURATION = 30 #in minutes
    uploadfile = myform.MyFile('uploadfile',
                           post='Longer recordings (of at least {0} minutes) are recommended. Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.'.format(MINDURATION),
                           description='Upload a .wav or .mp3 file. You may also upload a .zip or tar archive with multiple recordings.')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                              post='Long, single-speaker videos with no music work best.',
                              description='or copy and paste a link to a YouTube video:')
    dialect = form.Radio('dialect',
                         [('standard', 'Standard American '),
                          ('southern', 'Southern ')],
                         value = 'standard',
                         post='Selecting the appropriate dialect for the acoustic model may increase transcription accuracy. If your data contains speakers of multiple dialects, select Standard American. Other dialects may be added in the future.',
                         description='Dialect of the majority of speakers:')
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
    
    def speaker_form(self, completed_form, filenames, taskname): #send in the completed form too
      input_list = []
      numfiles = form.Hidden(name="numfiles",value=len(filenames))
      taskname = form.Hidden(name="taskname",value=taskname)
      input_list.extend([numfiles,taskname])
      for index in range(0, len(filenames)):

        if index!=0:
          checkBox = form.Checkbox(str(index),
                      class_='copy',
                      post='Check if speaker below is same as above')
          input_list.append(checkBox)
        filename = form.Hidden(value=filenames[index][0],name='filename'+str(index))
        speaker_name = form.Textbox('name'+str(index),
                         form.notnull,
                         pre="File Name: "+filenames[index][1],
                         description='Speaker ID')
        sex = myform.MyRadio('sex'+str(index),
                        [('M','Male', 'M'+str(index)),('F','Female', 'F'+str(index)),('C','Child', 'C'+str(index))],
                        description='Sex'
                        )

        input_list.extend([speaker_name,sex,filename])

      speakers = myform.ListToForm(input_list)
      s = speakers()
      # s.taskname.value = completed_form.taskname.value
      # s.filenames.value = len(filenames)


      return render.speakers(completed_form, s)
      
    def GET(self):
        self.dialect.value = 'standard'
        self.lw.value = '7' #defaults
        uploadsound = myform.MyForm(self.uploadfile, 
                                    self.filelink, 
                                    self.dialect, 
                                    self.lw, self.email, self.taskname, self.submit)
        form = uploadsound()
        return render.uploadsound(form, "")

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
            return render.uploadsound(form, "")

        else:
            #make taskname                                                                              
            taskname, audiodir, error = utilities.make_task(self.datadir)
            if error!="":
                form.note = error
                return render.uploadsound(form, "")
            
            form.taskname.value = taskname
            
            if x.filelink!="": 
                filename, error = utilities.youtube_wav(x.filelink, audiodir, taskname)
                if error!="":
                    form.note = error
                    return render.uploadsound(form, "")
        
                samprate, file_size, chunks, error = utilities.soxConversion(filename,
                                                                       audiodir, dochunk=20)
                if error!="":
                    form.note = error
                    return render.uploadsound(form, "")

                filenames = [(filename, x.filelink)]   #passed filename, display filename
                utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+filename+'.chunks'))
                
            elif 'uploadfile' in x:  
            
                #sanitize filename
                filename, extension = utilities.get_basename(x.uploadfile.filename)

                if extension not in ['.wav', '.zip', '.mp3', '.gz', '.tgz', '.tar']:
                    form.note = "Please upload a .wav, .mp3, .zip, .tgz, or .tar file."
                    return render.uploadsound(form, "")

                else:                
                    if extension in ['.zip', '.tar', '.tgz', '.gz']:
                        try:
                            if extension == '.zip':
                                z = zipfile.ZipFile(x.uploadfile.file)
                            else:
                                z = tarfile.open(fileobj=x.uploadfile.file)

                            total_size = 0.0

                            namelist = []
                            if extension == '.zip':
                                namelist = z.namelist()
                            else:
                                namelist = z.getnames()
                        
                            for subname in namelist:
                                subfilename, subextension = utilities.get_basename(subname)
                        
                                if subfilename in ['', '__MACOSX', '.DS_Store', '._']:
                                    continue
                        
                                if subextension not in ['.wav', '.mp3']:
                                    form.note = "Extension incorrect for file {0} in the folder {1}{2}. Make sure your folder only contains .wav or .mp3 files.".format(subfilename+subextension, filename, extension)
                                    return render.uploadsound(form, "")
                        
                                else:
                                    if extension == '.zip':
                                        samprate, file_size, chunks, error = utilities.process_audio(audiodir, subfilename, subextension, z.open(subname).read(), dochunk=20)
                                    else:
                                        samprate, file_size, chunks, error = utilities.process_audio(audiodir, subfilename, subextension, z.extractfile(subname).read(), dochunk=20)
                              
                                    if error!="":
                                        form.note = error
                                        return render.uploadsound(form, "")
                              
                                    utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+subfilename+'.chunks'))
                            
                                    filenames.append((subfilename, subfilename))
                                    total_size += file_size
                    
                        except:
                            form.note = "Could not read the archive file. Please check and upload again."
                            return render.uploadsound(form, "")
                  
                    else:  #will be mp3 or wav
                        samprate, file_size, chunks, error = utilities.process_audio(audiodir,
                                             filename, extension,
                                                                                     x.uploadfile.file.read(),
                                                                                     dochunk=20)
                    
                        if error!="":
                            form.note = error
                            return render.uploadsound(form, "")
                    
                        utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+filename+'.chunks'))
                    
                        filenames.append((filename, filename))
                        total_size = file_size
                
            if total_size < self.MINDURATION:  
                form.note = "Warning: Your files total only {:.2f} minutes of speech. We recommend at least {:.0f} minutes for best results.".format(total_size, self.MINDURATION)
                    
            #generate argument files
            utilities.gen_argfiles(self.datadir, form.taskname.value, filename, samprate, form.lw.value, form.dialect.value, form.email.value)
                    
            #show speaker form by adding fields to existing form and re-rendering
            return self.speaker_form(form, filenames, taskname)

class uploadtrans:
    uploadfile = myform.MyFile('uploadfile',
                           post='',
                           description='Your .wav or .mp3 file:')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                              post='',
                              description='or copy and paste a link to a YouTube video:')
    uploadtxtfile = myform.MyFile('uploadtxtfile',
                                 form.notnull,
                           post = 'Textgrid should contain a tier named "sentence" with sentence/breath group intervals.',
                           description='Manual transcription as a .TextGrid file:')
    email = form.Textbox('email',
                         form.notnull,
                         form.regexp(r'^[\w.+-]+@[\w.+-]+\.[\w.+-]+$',
                                     'Please enter a valid email address'),
                                     post='',
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
        index = 0
        filename = form.Hidden(value=filenames[index][0],name='filename'+str(index))
        speaker_name = form.Textbox('name'+str(index),
                         form.notnull,
                         pre="File Name: "+filenames[index][1],
                         description='Speaker ID')
        sex = myform.MyRadio('sex'+str(index),
                        [('M','Male', 'M'+str(index)),('F','Female', 'F'+str(index)),('C','Child', 'C'+str(index))],
                        description='Sex'
                        )

        input_list.extend([speaker_name,sex,filename])

        speakers = myform.ListToForm(input_list)
        s = speakers()

        return render.speakerstxt(completed_form, s)
    
    def GET(self):
        uploadsound = myform.MyForm(self.uploadfile,
                                    self.filelink, 
                                    self.uploadtxtfile,  
                                    self.email, self.taskname, self.submit)
        form = uploadsound()
        return render.uploadtxt(form, "")

    def POST(self):
        uploadtxt = myform.MyForm(self.uploadfile,
                                 self.filelink, 
                                 self.uploadtxtfile,  
                                 self.email, self.taskname, self.submit,
                                 validators = self.soundvalid)
        form = uploadtxt()      
        x = web.input(uploadfile={}, uploadtxtfile={})  

        if not form.validates(): #not validated
            return render.uploadtxt(form, "")

        filenames = []
        txtfilename, txtextension = utilities.get_basename(x.uploadtxtfile.filename)
        
        if txtextension != '.textgrid':  #TODO: check textgrid validity too
            form.note = 'Upload a transcript with a .TextGrid extension indicating sentence boundaries.'
            return render.uploadtxt(form, "")
        
        o = codecs.open(os.path.join(self.datadir, txtfilename+txtextension), 'w', 'utf8')
        o.write(x.uploadtxtfile.file.read())
        o.close()

        if 'uploadfile' in x:   
            #sanitize filename
            filename, extension = utilities.get_basename(x.uploadfile.filename)

            if extension not in ['.wav', '.mp3']:
                form.note = "Please upload a .wav or .mp3 file."
                return render.uploadtxt(form, "")

            else:
                #create new task                                                          
                taskname, audiodir, error = utilities.make_task(self.datadir)
                if error!="":
                    form.note = error
                    return render.uploadtxt(form, "")
                
                form.taskname.value = taskname
                
                chunks, error = utilities.write_sentgrid_as_lab(self.datadir, form.taskname.value, filename, txtfilename+txtextension, 'cmudict.forhtk.txt')
                if error!="":
                    form.note = error
                    return render.uploadtxt(form, "")
                
                samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                             filename, extension,
                    x.uploadfile.file.read(),
                    dochunk=chunks)
                if error!="":
                    form.note = error
                    return render.uploadtxt(form, "")
                
                utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+filename+'.chunks'))
                
                filenames.append((filename, filename))
        
        elif x.filelink!='':

            #make taskname
            taskname, audiodir, error = utilities.make_task(self.datadir)
            if error!="":
                    form.note = error
                    return render.uploadtxt(form, "")
            
            form.taskname.value = taskname

            filename = utilities.youtube_wav(x.filelink, audiodir, taskname)

            chunks, error = utilities.write_sentgrid_as_lab(self.datadir, form.taskname.value, filename, txtfilename+txtextension, 'cmudict.forhtk.txt')
            if error!="":
                form.note = error
                return render.uploadtxt(form, "")
            
            samprate, file_size, chunks, error = utilities.soxConversion(filename, audiodir, dochunk=chunks)
            if error!="":
                form.note = error
                return render.uploadtxt(form, "")
            
            utilities.write_chunks(chunks, os.path.join(self.datadir, taskname+filename+'.chunks'))
            
            filenames = [(filename, x.filelink)]
          
        utilities.gen_txtargfile(self.datadir, form.taskname.value, filename, samprate, form.email.value)
        
        return self.speaker_form(form, filenames, taskname)

class uploadtextgrid:
    uploadfile = myform.MyFile('uploadfile',
                           post='',
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
                                     post='',
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
        index = 0
        filename = form.Hidden(value=filenames[index][0],name='filename'+str(index))
        speaker_name = form.Textbox('name'+str(index),
                         form.notnull,
                         pre="File Name: "+filenames[index][1],
                         description='Speaker ID')
        sex = myform.MyRadio('sex'+str(index),
                        [('M','Male', 'M'+str(index)),('F','Female', 'F'+str(index)),('C','Child', 'C'+str(index))],
                        description='Sex'
                        )

        input_list.extend([speaker_name,sex,filename])

        speakers = myform.ListToForm(input_list)
        s = speakers()

        return render.speakersTG(completed_form, s)
    
    def GET(self):
        uploadsound = myform.MyForm(self.uploadfile,
                                    self.filelink, 
                                    self.uploadTGfile,  
                                    self.email, self.taskname, self.submit)
        form = uploadsound()
        return render.uploadTG(form, "")

    def POST(self):
        uploadTG = myform.MyForm(self.uploadfile,
                                 self.filelink, 
                                 self.uploadTGfile,  
                                 self.email, self.taskname, self.submit,
                                 validators = self.soundvalid)
        form = uploadTG()      
        x = web.input(uploadfile={}, uploadTGfile={})  

        if not form.validates(): #not validated
            return render.uploadTG(form, "")

        filenames = []
        tgfilename, tgextension = utilities.get_basename(x.uploadTGfile.filename)
        
        if tgextension != '.textgrid':
            form.note = 'Upload a file with a .TextGrid extension.'
            return render.uploadTG(form, "")

        if 'uploadfile' in x:   
            #sanitize filename
            filename, extension = utilities.get_basename(x.uploadfile.filename)
            
            if extension not in ['.wav', '.mp3']:
                form.note = "Please upload a .wav or .mp3 file."
                return render.uploadTG(form, "")

            else:
                #create new task                                                               
                taskname, audiodir, error = utilities.make_task(self.datadir)
                if error!="":
                    form.note = error
                    return render.uploadTG(form, "")
                
                form.taskname.value = taskname
                
                samprate, total_size, chunks, error = utilities.process_audio(audiodir,
                                             filename, extension,
                    x.uploadfile.file.read(),
                    dochunk=None)

                if error!="":
                    form.note = error
                    return render.uploadTG(form, "")

                filenames.append((filename, filename))
        
        elif x.filelink!='':

            #make taskname
            taskname, audiodir, error = utilities.make_task(self.datadir)
            if error!="":
                    form.note = error
                    return render.uploadTG(form, "")
            
            form.taskname.value = taskname

            filename = utilities.youtube_wav(x.filelink, audiodir, taskname)
            samprate, file_size, chunks, error = utilities.soxConversion(filename, audiodir, dochunk=None)
            if error!="":
                form.note = error
                return render.uploadTG(form, "")
            
            filenames = [(filename, x.filelink)]
        
        utilities.write_textgrid(self.datadir, form.taskname.value, filename, x.uploadTGfile.file.read()) 

        utilities.gen_tgargfile(self.datadir, form.taskname.value, filename, form.email.value)
        
        return self.speaker_form(form, filenames, taskname)

class uploadeval:
    reffile = myform.MyFile('reffile',
                            form.notnull,
                            post = '',
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
