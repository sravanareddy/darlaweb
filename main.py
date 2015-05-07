#!/usr/bin/env python

import web
import shutil
from web import form
import myform
import utilities
import zipfile
from align import app_align

render = web.template.render('templates/', base='layout')

urls = ('/', 'index', '/upload', 'upload', '/align', 'app_align')
app = web.application(urls, globals())
web.config.debug = True
        
class index:
    def GET(self):
        return render.index()

class upload:
    MINDURATION = 30 #in minutes
    uploadfile = myform.MyFile('uploadfile',
                           post='Longer recordings (of at least {0} minutes) are recommended. Your uploaded files are stored temporarily on the Dartmouth servers in order to process your job, and deleted after.'.format(MINDURATION),
                           description='Upload a .wav, .mp3, or .zip file with multiple recordings')
    filelink = form.Textbox('filelink',
                            form.regexp(r'^$|https\://www\.youtube\.com/watch\?v\=\S+', 'Check your link. It should start with https://www.youtube.com/watch?v='),
                              post='Long, single-speaker videos with no music work best.',
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
    
    soundvalid = [form.Validator('Please upload a file or enter a video link (but not both).',
                                 lambda x: (x.filelink!='' or x.uploadfile) and not (x.uploadfile and x.filelink!=''))]
    
    datadir = open('filepaths.txt').read().strip()
    
    def speaker_form(self, filenames):
      input_list = []
      for index in filenames:

        speaker_name = form.Textbox('name'+str(index),
                         form.notnull,
                         description='Speaker ID')
        sex = form.Radio('sex', 
                        [('M','Male'),('F','Female'),('C','Child')],
                        description='Sex')
        input_list.extend([speaker_name,sex])
        if index!=0:
          checkBox = form.Checkbox(str(index),
                      class_='copy')
          input_list.append(checkBox)

      speakers = myform.MyForm(input_list[0]) #can you pass in a list of things as the form? hopefully :( right now not working though 
      s = speakers() 
      
      #if can use a lambda function, will use. speakers = myform.MyForm(input_list lambda), if not, code in html...
      return render.speakers(filenames, "") #coding in html currently

    def GET(self):
        self.dialect.value = 'standard'
        self.lw.value = '7' #defaults
        uploadsound = myform.MyForm(self.uploadfile, 
                                    self.filelink, 
                                    self.dialect, 
                                    self.lw, self.email, self.taskname)
        form = uploadsound()
        return render.formtest(form, "")

    def POST(self):
        uploadsound = myform.MyForm(self.uploadfile, 
                                    self.filelink, 
                                    self.dialect, 
                                    self.lw, self.email, self.taskname,
                                    validators = self.soundvalid)
        form = uploadsound()
        x = web.input(uploadfile={})
        filenames = [] # for use in speaker form
        
        if not form.validates(): #not validated
            return render.formtest(form, "")

        elif x.filelink!="": 
          #make taskname
          # taskname, audiodir = utilities.make_task(self.datadir)
          # self.taskname.value = taskname

          # filename = utilities.youtube_wav(url, taskname)
          filename = "ytvideo"
          filenames = [filename]
          # samprate = utilities.soxConversion(audiodir,
          #                                    filename)

          # return "Success! your file {0} has a sampling rate of {1}. Your email: {2}".format(filename, samprate, form.email.value)
          #return new form
          return self.speaker_form(filenames)
        
        elif 'uploadfile' in x:  
            
            #sanitize filename
            filename, extension = utilities.get_basename(x.uploadfile.filename)

            if extension not in ['.wav', '.zip', '.mp3']:
                form.note = "Please upload a .wav, .mp3, or .zip file"
                return render.formtest(form, "")

            else:
                #create new task                                                               
                taskname, audiodir = utilities.make_task(self.datadir)
                form.taskname.value = taskname
                
                if extension == '.zip': #extract zip contents
                    z = zipfile.ZipFile(x.uploadfile.file)

                    total_size = 0.0
                    
                    for subname in z.namelist():
                        subfilename, subextension = utilities.get_basename(subname)
                        print subfilename, subextension
                        
                        if subfilename in ['', '__MACOSX', '.DS_Store', '._']:
                            continue
                        
                        if subextension not in ['.wav', '.mp3']:
                            form.note = "Extension incorrect for file {0} in the zip folder {1}.zip. Make sure your folder only contains .wav or .mp3 files.".format(subfilename+subextension, filename)
                            return render.formtest(form, "")
                        
                        else:
                            samprate, file_size = utilities.process_audio(audiodir,
                                                     subfilename, subextension,
                                z.open(subname).read())
                            
                            filenames.append(subfilename)
                            total_size += file_size

                else:  #will be mp3 or wav
                    samprate, total_size = utilities.process_audio(audiodir,
                                             filename, extension,
                        x.uploadfile.file.read())
                    filenames.append(filename)
                
                if total_size < self.MINDURATION:  #TODO: ensure that this re-renders (perhaps with speakers)
                        form.note = "Warning: Your files total only {0} minutes of speech. We recommend at least {1} minutes for best results.".format(total_size, self.MINDURATION)
                    
                #generate ctl files
                utilities.gen_argfiles(self.datadir, form.taskname.value, filename, samprate, form.lw.value, form.dialect.value, form.email.value)
                    
                #TODO: show speaker form by adding fields to existing form and re-rendering (?)
                return "Success!"

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()

