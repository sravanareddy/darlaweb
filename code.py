#!/usr/bin/env python

import web
import shutil
from web import form
import myform

render = web.template.render('templates/', base='layout')

urls = ('/', 'index', '/upload', 'upload')
app = web.application(urls, globals())
web.config.debug = True
    
uploadfile = form.File('uploadfile',
                       post='Longer recordings (of at least 30 minutes) are recommended. Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.',
                       description='Upload a .wav, .mp3, or .zip file with multiple recordings',)

dialect = form.Radio('dialect',
                     [('standard', 'Standard American '),
                      ('southern', 'Southern ')],
                     post='Selecting the appropriate dialect for the acoustic model may increase transcription accuracy. If your data contains speakers of multiple dialects, select Standard American. Other dialects may be added in the future.',
                     description='Dialect of the majority of speakers')

lw = form.Radio('lw',
               [(7, 'Free speech or reading passage '),
                (3, 'Word list ')],
                post='If your recording contains both styles, select the free speech option.',
                description='Speech Type',)

email = form.Textbox('email',
                     form.regexp(r"^[\w.+-]+@[\w.+-]+\.[\w.+-]+$", 
                                 "Please enter a valid email address"),
                     post='We will not store or distribute your address.',
                     description='Your e-mail address')

uploadsound = myform.MyForm(uploadfile, dialect, lw, email)
    
class index:
    def GET(self):
        return render.index()

class upload: 
    def GET(self): 
        form = uploadsound()
        # make sure you create a copy of the form by calling it (line above)
        # Otherwise changes will appear globally
        return render.formtest(form)

    def POST(self): 
        form = uploadsound() 
        if not form.validates(): 
            return render.formtest(form)
        else:
            # form.d.boe and form['boe'].value are equivalent ways of
            # extracting the validated arguments from the form.
            return render.formtest("Grreat success! email: {0}".format(form['email'].value))

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()

