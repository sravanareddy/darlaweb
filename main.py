#!/usr/bin/env python

import web
import shutil
from web import form
import myform
import utilities
import os

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
    
    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).', lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]   #TODO: why doesn't this work?
    
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
                                    self.lw, self.email, self.taskname)
        form = uploadsound()
        x = web.input(uploadfile={})
        if not form.validates(): 
            return render.formtest(form)
        
        elif 'uploadfile' in x:  #TODO: handle mp3 and zip files
            
            #create new task                                                               
            taskname, audiodir = utilities.make_task(self.datadir)
            self.taskname.value = taskname
            
            #sanitize filename
            filename = utilities.get_basename(x.uploadfile.filename)
            
            #write contents of file
            o = open(os.path.join(audiodir, filename), 'w')
            o.write(x.uploadfile.file.read())
            o.close()

            #split and convert frequency
            samprate, filesize, rate = utilities.soxConversion(filename, audiodir)
            
            return "Great success! your file: {0} has a sampling rate of {1}. Your email: {2}".format(filename, samprate, form.email.value)            
    
if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()

