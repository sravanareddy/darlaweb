#!/usr/bin/env python

import web
import shutil
from web import form
import myform
import utilities
import zipfile
import tarfile
import align

render = web.template.render('templates/', base='layout')

urls = ('/', 'index', '/upload', 'upload', '/uploadtrans', 'uploadtrans', '/align', align.app_align)
app = web.application(urls, globals())
web.config.debug = True
        
class index:
    def GET(self):
        return render.index()

class upload:
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
    
    datadir = open('filepaths.txt').read().strip()
    
    def speaker_form(self, completed_form, filenames): #send in the completed form too
      input_list = []
      for index in range(0, len(filenames)):

        #filenames = form.Hidden()
        if index!=0:
          checkBox = form.Checkbox(str(index),
                      class_='copy',
                      post='Check if speaker is same as above')
          input_list.append(checkBox)

        speaker_name = form.Textbox('name'+str(index),
                         form.notnull,
                         pre="File Name:"+filenames[index],
                         description='Speaker ID')
        sex = form.Radio('sex'+str(index), 
                        [('M','Male'),('F','Female'),('C','Child')],
                        description='Sex'
                        )

        input_list.extend([speaker_name,sex])

      speakers = myform.ListToForm(input_list)
      s = speakers()

      return render.speakers(completed_form, s) #TODO: send in disabled form
      # return render.formtest(completed_form,s)

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

        elif x.filelink!="": 
          #make taskname
          taskname, audiodir = utilities.make_task(self.datadir)
          form.taskname.value = taskname

          filename = utilities.youtube_wav(x.filelink, audiodir, taskname)
          samprate, file_size = utilities.soxConversion(filename,
                                             audiodir)
          filenames = [filename, filename]

          utilities.gen_argfiles(self.datadir, form.taskname.value, filename, samprate, form.lw.value, form.dialect.value, form.email.value)
          form.note = "Warning: Your files total only {:.2f} minutes of speech. We recommend at least {:.2f} minutes for best results.".format(file_size, self.MINDURATION)
          # return "Success! your file {0} has a sampling rate of {1}. Your email: {2}".format(filename, samprate, form.email.value)
          #return new form? 
          return self.speaker_form(form, filenames)

        
        elif 'uploadfile' in x:  
            
            #sanitize filename
            filename, extension = utilities.get_basename(x.uploadfile.filename)

            if extension not in ['.wav', '.zip', '.mp3', '.gz', '.tgz', '.tar']:
                form.note = "Please upload a .wav, .mp3, .zip, .tgz, or .tar file."
                return render.uploadsound(form, "")

            else:
                #create new task                                                               
                taskname, audiodir = utilities.make_task(self.datadir)
                form.taskname.value = taskname
                
                if extension in ['.zip', '.tar', '.tgz', '.gz']:
                    #TODO: try-except in case there's a problem with the file or a mismatch of the type with the extension
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

                            return self.speaker_form(form, filenames)
                        
                        else:
                            if extension == '.zip':
                                samprate, file_size = utilities.process_audio(audiodir,
                                                     subfilename, subextension,
                                    z.open(subname).read())
                            else:
                                samprate, file_size = utilities.process_audio(audiodir,
                                                     subfilename, subextension,
                                    z.extractfile(subname).read())
                            
                            filenames.append(subfilename)
                            total_size += file_size
                                            
                else:  #will be mp3 or wav
                    samprate, total_size = utilities.process_audio(audiodir,
                                             filename, extension,
                        x.uploadfile.file.read())
                    filenames.append(filename)
                
                if total_size < self.MINDURATION:  #TODO: ensure that this re-renders (perhaps with speakers)
                        form.note = "Warning: Your files total only {:.0f} minutes of speech. We recommend at least {:.0f} minutes for best results.".format(total_size, self.MINDURATION)
                    
                #generate argument files
                utilities.gen_argfiles(self.datadir, form.taskname.value, filename, samprate, form.lw.value, form.dialect.value, form.email.value)
                    
                #show speaker form by adding fields to existing form and re-rendering
                return self.speaker_form(form, filenames)

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()

class uploadtrans:
    uploadfile = myform.MyFile('uploadfile',
                           post='',
                           description='Your .wav or .mp3 file')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                              post='',
                              description='or copy and paste a link to a YouTube video:')
    uploadTGfile = myform.MyFile('uploadTGfile',
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
        x = web.input(uploadfile={})  

        if not form.validates(): #not validated
            return render.uploadsound(form, "")

        if self.uploadTGfile in x:
            #sanitize filename
            TGfilename, TGextension = utilities.get_basename(x.uploadTGfile.filename)


            if TGextension!='.TextGrid':
                form.note = "Please upload a .TextGrid file."
                return render.uploadTG(form, "")

            elif x.filelink!='':

                #make taskname
                taskname, audiodir = utilities.make_task(self.datadir)
                form.taskname.value = taskname

                filename = utilities.youtube_wav(x.filelink, audiodir, taskname)
                samprate, file_size = utilities.soxConversion(filename, audiodir)

                utilities.gen_argfiles(self.datadir, form.taskname.value, filename, samprate, '', '', form.email.value)
                form.note = "Success! your file {0} has a sampling rate of {1}. Your email: {2}".format(filename, samprate, form.email.value)
                #return new form? 

            elif 'uploadfile' in x:

                #sanitize filename
                filename, extension = utilities.get_basename(x.uploadfile.filename)


                if extension not in ['.wav', '.mp3']:
                    form.note = "Please upload a .wav or .mp3"
                    return render.uploadTG(form, "")

                else:
                    samprate, total_size = utilities.process_audio(audiodir,
                                             filename, extension,
                        x.uploadfile.file.read())
                
                    #generate argument files
                    utilities.gen_argfiles(self.datadir, form.taskname.value, filename, samprate, '', '', form.email.value)
                    form.note = "Success! your file {0} has a sampling rate of {1}. Your email: {2}".format(filename, samprate, form.email.value)
        else:
            if 'uploadfile' in x or x.filelink!='':
                form.note = "Please upload a .TextGrid file."
                return render.uploadTG(form, "")




