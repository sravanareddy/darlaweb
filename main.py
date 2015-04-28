#!/usr/bin/env python

import web
import shutil
from web import form
import myform
import utilities
import os
import zipfile

render = web.template.render('templates/', base='layout')

urls = ('/', 'index', '/upload', 'upload')
app = web.application(urls, globals())
web.config.debug = True
        
class index:
    def GET(self):
        return render.index()

class upload:
    uploadfile = myform.MyFile('uploadfile',
                           post='Longer recordings (of at least 30 minutes) are recommended. Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.',
                           description='Upload a .wav, .mp3, or .zip file with multiple recordings')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                              post='Long, single-speaker videos with no music work best',
                              description='or copy and paste a link to a YouTube video')
    dialect = form.Radio('dialect',
                         [('standard', 'Standard American '),
                          ('southern', 'Southern ')],
                         value = 'standard',
                         post='Selecting the appropriate dialect for the acoustic model may increase transcription accuracy. If your data contains speakers of multiple dialects, select Standard American. Other dialects may be added in the future.',
                         description='Dialect of the majority of speakers')
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
                         description='Your e-mail address')
    taskname = form.Hidden('taskname')
    
    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).', lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]
    
    datadir = open('filepaths.txt').read().strip()
    
    def GET(self):
        self.dialect.value = 'standard'
        self.lw.value = '7' #defaults
        uploadsound = myform.MyForm(self.uploadfile, 
                                    self.filelink, 
                                    self.dialect, 
                                    self.lw, self.email, self.taskname)
        form = uploadsound()
        return render.formtest(form)

    def POST(self):
        uploadsound = myform.MyForm(self.uploadfile, 
                                    self.filelink, 
                                    self.dialect, 
                                    self.lw, self.email, self.taskname,
                                    validators = self.soundvalid)
        form = uploadsound()
        x = web.input(uploadfile={})
        
        if not form.validates(): #not validated
            return render.formtest(form)

        elif x.filelink!="": #TODO - youtube files
          #make taskname
          taskname, audiodir = utilities.make_task(self.datadir)
          self.taskname.value = taskname
          filename = utilities.youtube_wav(url, taskname)
          return "Youtube" 
        
        elif 'uploadfile' in x:  #TODO: handle mp3 files
                        
            #sanitize filename
            filename, extension = utilities.get_basename(x.uploadfile.filename)

            if extension not in ['.wav', '.zip', '.mp3']:
                return "File type should be wav, mp3, or zip." #TODO: make this an in-form error

            else:
                #create new task                                                               
                taskname, audiodir = utilities.make_task(self.datadir)
                self.taskname.value = taskname
                
                if extension == '.zip': #extract zip contents
                    z = zipfile.ZipFile(x.uploadfile.file)
                    filecount = 0
                    for subname in z.namelist():
                        subfilename, subextension = utilities.get_basename(subname)
                        
                        if subfilename in ['', '__MACOSX', '.DS_Store']:
                            continue
                        
                        if subextension not in ['.wav', '.mp3']:
                            return "Extension incorrect for file {0} in the zip folder {1}.zip. Make sure your folder only contains .wav or .mp3 files.".format(subname, filename)   #TODO: make this an in-form error or just ignore this file without raising an error
                        else:
                            samprate = utilities.process_audio(audiodir,
                                                     subfilename, subextension,
                                z.open(subname).read())
                            filecount += 1

                    return "Success! your file {0} contains {1} files. Your email: {2}".format(filename, filecount, form.email.value)

                else:  #wav or mp3
                    samprate = utilities.process_audio(audiodir,
                                             filename, extension,
                        x.uploadfile.file.read())
                
                    return "Success! your file {0} has a sampling rate of {1}. Your email: {2}".format(filename, samprate, form.email.value)              
    
if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()

