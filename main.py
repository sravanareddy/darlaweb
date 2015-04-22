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
    uploadsound = myform.MyForm(uploadfile, 
                                filelink, 
                                dialect, 
                                lw, 
                                email, 
                                validators=[form.Validator('Please upload a file or enter a video link.', lambda x: x.uploadfile or x.filelink), 
                                            form.Validator('Upload a file OR select a YouTube video, not both.', lambda x: not (x.uploadfile and x.filelink))])
    
    datadir = open('filepaths.txt').read().strip()
    
    def GET(self):
        form = self.uploadsound()
        return render.formtest(form)

    def POST(self): 
        form = self.uploadsound()
        x = web.input(uploadfile={})
        if not form.validates(): #TODO: can't display uploaded filename.
            return render.formtest(form)
        else:
            #create new task                                                               
            taskname = utilities.make_task(self.datadir)
            #sanitize filename
            filename = utilities.get_basename(x.uploadfile.filename)
            #write contents of file
            o = open(os.path.join(self.datadir, taskname+'.wav', filename), 'w')
            o.write(x.uploadfile.file.read())
            o.close()
        
            #disable form
            form.disable()
            
            return render.formtest(form)

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()

